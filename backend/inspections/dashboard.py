"""Staff web dashboard: map, priority list, asset and inspection review."""

import csv
from datetime import timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import ValidationError
from django.db.models import Count, Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from ml.risk.severity import LABELS, MIN_CONFIDENCE, assess

from .health_service import asset_health
from .models import Infrastructure, Inspection
from .services import delete_inspection

DISPLAY_TZ = "Asia/Kolkata"  # how dates are shown in the pages (CSV uses UTC)

RISK_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]  # worst first
LEVEL_COLORS = {
    "LOW": "#2e7d32",
    "MEDIUM": "#f9a825",
    "HIGH": "#ef6c00",
    "CRITICAL": "#c62828",
}
NO_DATA_COLOR = "#9e9e9e"
DAMAGE_COLORS = {
    "pothole": "#e53935",
    "longitudinal_crack": "#fdd835",
    "transverse_crack": "#d81b60",
    "alligator_crack": "#fb8c00",
}


# ---- access control -------------------------------------------------------


def staff_required(view):
    return user_passes_test(
        lambda user: user.is_active and user.is_staff,
        login_url="dashboard-login",
    )(view)


class StaffAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise ValidationError(
                "This account does not have dashboard access.",
                code="no_dashboard_access",
            )


class DashboardLoginView(LoginView):
    template_name = "dashboard/login.html"
    authentication_form = StaffAuthenticationForm
    # Off on purpose: a signed-in non-staff user would otherwise bounce
    # between the login page and the dashboard forever.
    redirect_authenticated_user = False
    next_page = "dashboard-overview"


class DashboardLogoutView(LogoutView):
    next_page = "dashboard-login"


# ---- helpers --------------------------------------------------------------


def _display_name(asset):
    # Name set by staff, else the place name from the phone, else "Asset #id".
    return asset.display_name


def _risk_param(request):
    value = request.GET.get("risk", "").upper()
    return value if value in RISK_ORDER else ""


def _filter_rows(rows, risk):
    return [r for r in rows if not risk or r["risk"] == risk]


def _asset_rows():
    """One row per asset, worst health first. Assets with no inspections last."""
    assets = Infrastructure.objects.annotate(
        inspection_count=Count("inspections"),
        last_inspected=Max("inspections__created_at"),
    )
    rows = []
    for asset in assets:
        health = asset_health(asset)
        latest = asset.inspections.order_by("-created_at").first()
        latest_assessment = (
            assess(latest.detections, latest.image_width, latest.image_height)
            if latest is not None
            else None
        )
        risk = health["risk_level"] if health else None
        rows.append(
            {
                "asset": asset,
                "name": _display_name(asset),
                "url": reverse("dashboard-asset", args=[asset.pk]),
                "risk": risk,
                "color": LEVEL_COLORS.get(risk, NO_DATA_COLOR),
                "score": health["health_score"] if health else None,
                "trend": health["trend"] if health else None,
                "inspection_count": asset.inspection_count,
                "last_inspected": asset.last_inspected,
                "latest_severity": (
                    latest_assessment["severity_score"] if latest_assessment else None
                ),
                "latest_finding": (
                    latest_assessment["reasons"][0] if latest_assessment else None
                ),
            }
        )
    rows.sort(
        key=lambda r: (101 if r["score"] is None else r["score"], r["name"].lower())
    )
    return rows


def _csv_safe(value):
    """Stop spreadsheet apps from running a name like =HYPERLINK(...) as a formula."""
    text = "" if value is None else str(value)
    if text and text[0] in "=+-@\t\r":
        return "'" + text
    return text


# ---- overview -------------------------------------------------------------


@staff_required
def overview(request):
    risk = _risk_param(request)
    all_rows = _asset_rows()
    rows = _filter_rows(all_rows, risk)

    counts = {level: 0 for level in RISK_ORDER}
    for r in all_rows:
        if r["risk"]:
            counts[r["risk"]] += 1

    map_points = [
        {
            "name": r["name"],
            "lat": r["asset"].latitude,
            "lon": r["asset"].longitude,
            "color": r["color"],
            "url": r["url"],
            "summary": (
                f"{r['risk']} risk · health {r['score']}"
                if r["risk"]
                else "No inspections yet"
            ),
        }
        for r in rows
    ]

    now = timezone.now()
    context = {
        "tz": DISPLAY_TZ,
        "rows": rows,
        "risk": risk,
        "levels": RISK_ORDER,
        "counts": [
            {"level": lvl, "n": counts[lvl], "color": LEVEL_COLORS[lvl]}
            for lvl in RISK_ORDER
        ],
        "total_assets": len(all_rows),
        "unassessed": sum(1 for r in all_rows if r["risk"] is None),
        "total_inspections": Inspection.objects.count(),
        "week_inspections": Inspection.objects.filter(
            created_at__gte=now - timedelta(days=7)
        ).count(),
        "map_points": map_points,
    }
    return render(request, "dashboard/overview.html", context)


# ---- asset ----------------------------------------------------------------


class AssetForm(forms.ModelForm):
    class Meta:
        model = Infrastructure
        fields = ["name", "asset_type", "construction_year"]

    def clean_construction_year(self):
        year = self.cleaned_data.get("construction_year")
        if year is not None and not (1800 <= year <= timezone.now().year):
            raise ValidationError(
                f"Enter a year between 1800 and {timezone.now().year}."
            )
        return year


@staff_required
def asset_detail(request, pk):
    asset = get_object_or_404(Infrastructure, pk=pk)

    if request.method == "POST":
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, "Asset updated.")
            return redirect("dashboard-asset", pk=asset.pk)
    else:
        form = AssetForm(instance=asset)

    # Re-read so a rejected form never leaks half-applied values into the page.
    asset = Infrastructure.objects.get(pk=pk)
    health = asset_health(asset)

    items = []
    for inspection in asset.inspections.select_related("inspector").order_by(
        "-created_at"
    )[:50]:
        a = assess(inspection.detections, inspection.image_width, inspection.image_height)
        items.append(
            {
                "inspection": inspection,
                "score": a["severity_score"],
                "priority": a["priority"],
                "color": LEVEL_COLORS[a["priority"]],
                "detections": len(inspection.detections),
            }
        )

    context = {
        "tz": DISPLAY_TZ,
        "asset": asset,
        "name": _display_name(asset),
        "health": health,
        "risk": health["risk_level"] if health else None,
        "form": form,
        "items": items,
        "history": list(reversed(items[:30])),  # oldest to newest, for the chart
    }
    return render(request, "dashboard/asset_detail.html", context)


# ---- inspection -----------------------------------------------------------


@staff_required
def inspection_detail(request, pk):
    inspection = get_object_or_404(
        Inspection.objects.select_related("infrastructure", "inspector"), pk=pk
    )
    assessment = assess(
        inspection.detections, inspection.image_width, inspection.image_height
    )
    asset = inspection.infrastructure
    health = asset_health(asset) if asset is not None else None

    width = inspection.image_width or 1
    height = inspection.image_height or 1
    boxes = []
    for d in inspection.detections:
        x1, y1, x2, y2 = d["bounding_box"]
        kind = d["damage_type"]
        confidence = d["confidence"]
        boxes.append(
            {
                "label": LABELS.get(kind, kind).capitalize(),
                "confidence_pct": round(confidence * 100),
                "counted": confidence >= MIN_CONFIDENCE,
                "color": DAMAGE_COLORS.get(kind, "#ffffff"),
                "left": x1 / width * 100,
                "top": y1 / height * 100,
                "width": (x2 - x1) / width * 100,
                "height": (y2 - y1) / height * 100,
            }
        )

    context = {
        "tz": DISPLAY_TZ,
        "inspection": inspection,
        "asset": asset,
        "asset_name": _display_name(asset) if asset is not None else "No asset",
        "assessment": assessment,
        "priority_color": LEVEL_COLORS[assessment["priority"]],
        "health": health,
        "health_color": LEVEL_COLORS.get(health["risk_level"]) if health else None,
        "boxes": boxes,
        "has_faded": any(not b["counted"] for b in boxes),
        "min_confidence_pct": round(MIN_CONFIDENCE * 100),
    }
    return render(request, "dashboard/inspection_detail.html", context)


@staff_required
@require_POST
def inspection_delete(request, pk):
    inspection = get_object_or_404(Inspection.objects.select_related("infrastructure"), pk=pk)
    inspection_id = inspection.pk
    asset_id, asset_removed = delete_inspection(inspection)
    messages.success(request, f"Inspection #{inspection_id} deleted.")
    if asset_id is None or asset_removed:
        return redirect("dashboard-overview")
    return redirect("dashboard-asset", pk=asset_id)


# ---- export ---------------------------------------------------------------


@staff_required
def export_assets(request):
    rows = _filter_rows(_asset_rows(), _risk_param(request))

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="infraintel-assets-{timezone.now():%Y%m%d}.csv"'
    )
    response.write("\ufeff")  # byte-order mark so Excel reads UTF-8 correctly
    writer = csv.writer(response)
    writer.writerow(
        [
            "priority_rank",
            "id",
            "name",
            "type",
            "latitude",
            "longitude",
            "construction_year",
            "risk_level",
            "health_score",
            "trend",
            "inspections_total",
            "last_inspected_utc",
            "latest_severity",
            "latest_finding",
        ]
    )
    for rank, r in enumerate(rows, start=1):
        a = r["asset"]
        writer.writerow(
            [
                rank if r["score"] is not None else "",
                a.pk,
                _csv_safe(r["name"]),
                a.asset_type,
                a.latitude,
                a.longitude,
                a.construction_year or "",
                r["risk"] or "",
                "" if r["score"] is None else r["score"],
                r["trend"] or "",
                r["inspection_count"],
                r["last_inspected"].isoformat() if r["last_inspected"] else "",
                "" if r["latest_severity"] is None else r["latest_severity"],
                _csv_safe(r["latest_finding"]),
            ]
        )
    return response