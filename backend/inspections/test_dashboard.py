import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Infrastructure, Inspection

User = get_user_model()

FULL = (0, 0, 100, 100)


def detection(kind, confidence, box):
    return {
        "damage_type": kind,
        "confidence": confidence,
        "bounding_box": list(box),
        "source_model": "test",
    }


def make_inspection(asset, detections, inspector=None):
    return Inspection.objects.create(
        inspector=inspector,
        infrastructure=asset,
        image="inspections/test.png",
        latitude=asset.latitude,
        longitude=asset.longitude,
        image_width=100,
        image_height=100,
        detections=detections,
    )


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="infraintel-dash-media-"))
class DashboardTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            "boss", password="pw-boss-1234", is_staff=True
        )
        self.inspector = User.objects.create_user("alice", password="pw-alice-123")

        self.bad = Infrastructure.objects.create(
            name="Bad road", latitude=23.0, longitude=77.0
        )
        self.fine = Infrastructure.objects.create(
            name="Fine road", latitude=23.1, longitude=77.1
        )
        self.bad_inspection = make_inspection(
            self.bad,
            [detection("alligator_crack", 0.9, FULL), detection("pothole", 0.9, FULL)],
            self.inspector,
        )
        self.fine_inspection = make_inspection(
            self.fine, [detection("pothole", 0.9, (0, 0, 10, 10))], self.inspector
        )

    # ---- access ----------------------------------------------------------

    def test_anonymous_is_redirected_to_login(self):
        r = self.client.get(reverse("dashboard-overview"))
        self.assertRedirects(
            r,
            f"{reverse('dashboard-login')}?next={reverse('dashboard-overview')}",
        )

    def test_login_page_renders(self):
        self.assertEqual(self.client.get(reverse("dashboard-login")).status_code, 200)

    def test_staff_can_log_in(self):
        r = self.client.post(
            reverse("dashboard-login"),
            {"username": "boss", "password": "pw-boss-1234"},
        )
        self.assertRedirects(r, reverse("dashboard-overview"))

    def test_non_staff_cannot_log_in(self):
        r = self.client.post(
            reverse("dashboard-login"),
            {"username": "alice", "password": "pw-alice-123"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_non_staff_session_is_blocked(self):
        self.client.force_login(self.inspector)
        r = self.client.get(reverse("dashboard-overview"))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("dashboard-login"), r["Location"])

    def test_logout(self):
        self.client.force_login(self.staff)
        r = self.client.post(reverse("dashboard-logout"))
        self.assertRedirects(r, reverse("dashboard-login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    # ---- overview --------------------------------------------------------

    def test_overview_lists_worst_asset_first(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse("dashboard-overview"))
        self.assertEqual(r.status_code, 200)
        rows = r.context["rows"]
        self.assertEqual([row["name"] for row in rows], ["Bad road", "Fine road"])
        self.assertEqual(rows[0]["risk"], "CRITICAL")
        self.assertEqual(rows[1]["risk"], "LOW")
        self.assertContains(r, "Bad road")

    def test_risk_filter(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse("dashboard-overview"), {"risk": "critical"})
        self.assertEqual([row["name"] for row in r.context["rows"]], ["Bad road"])

    def test_invalid_risk_filter_is_ignored(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse("dashboard-overview"), {"risk": "bogus"})
        self.assertEqual(len(r.context["rows"]), 2)

    # ---- asset -----------------------------------------------------------

    def test_asset_detail_renders(self):
        self.client.force_login(self.staff)
        r = self.client.get(reverse("dashboard-asset", args=[self.bad.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Bad road")

    def test_asset_edit_updates_the_asset(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard-asset", args=[self.bad.pk])
        r = self.client.post(
            url,
            {"name": "Ring Road", "asset_type": "road", "construction_year": "1998"},
        )
        self.assertRedirects(r, url)
        self.bad.refresh_from_db()
        self.assertEqual(self.bad.name, "Ring Road")
        self.assertEqual(self.bad.construction_year, 1998)

    def test_asset_edit_rejects_a_future_year(self):
        self.client.force_login(self.staff)
        r = self.client.post(
            reverse("dashboard-asset", args=[self.bad.pk]),
            {"name": "Ring Road", "asset_type": "road", "construction_year": "3000"},
        )
        self.assertEqual(r.status_code, 200)
        self.bad.refresh_from_db()
        self.assertEqual(self.bad.name, "Bad road")
        self.assertIsNone(self.bad.construction_year)

    # ---- inspection ------------------------------------------------------

    def test_inspection_detail_renders_with_boxes(self):
        self.client.force_login(self.staff)
        r = self.client.get(
            reverse("dashboard-inspection", args=[self.bad_inspection.pk])
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context["boxes"]), 2)

    def test_delete_requires_post(self):
        self.client.force_login(self.staff)
        r = self.client.get(
            reverse("dashboard-inspection-delete", args=[self.bad_inspection.pk])
        )
        self.assertEqual(r.status_code, 405)
        self.assertTrue(Inspection.objects.filter(pk=self.bad_inspection.pk).exists())

    def test_delete_keeps_a_curated_asset(self):
        self.client.force_login(self.staff)
        r = self.client.post(
            reverse("dashboard-inspection-delete", args=[self.bad_inspection.pk])
        )
        self.assertRedirects(r, reverse("dashboard-asset", args=[self.bad.pk]))
        self.assertFalse(Inspection.objects.filter(pk=self.bad_inspection.pk).exists())
        self.assertTrue(Infrastructure.objects.filter(pk=self.bad.pk).exists())

    def test_delete_removes_an_auto_created_asset(self):
        auto = Infrastructure.objects.create(
            latitude=10.0, longitude=10.0, auto_created=True
        )
        inspection = make_inspection(auto, [detection("pothole", 0.9, FULL)])
        self.client.force_login(self.staff)
        r = self.client.post(reverse("dashboard-inspection-delete", args=[inspection.pk]))
        self.assertRedirects(r, reverse("dashboard-overview"))
        self.assertFalse(Infrastructure.objects.filter(pk=auto.pk).exists())

    def test_non_staff_cannot_delete(self):
        self.client.force_login(self.inspector)
        r = self.client.post(
            reverse("dashboard-inspection-delete", args=[self.bad_inspection.pk])
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Inspection.objects.filter(pk=self.bad_inspection.pk).exists())

    # ---- export ----------------------------------------------------------

    def test_csv_export_neutralises_formula_names(self):
        self.fine.name = "=1+1"
        self.fine.save()
        self.client.force_login(self.staff)
        r = self.client.get(reverse("dashboard-export-assets"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/csv", r["Content-Type"])
        text = r.content.decode("utf-8-sig")
        self.assertIn("priority_rank,id,name", text)
        self.assertIn("'=1+1", text)
        self.assertIn("Bad road", text)