from datetime import date

from ml.risk.health import assess_health
from ml.risk.severity import assess


def asset_health(infrastructure, window: int = 10):
    """Health for an asset from its recent inspections, or None if it has none.

    Several inspections on the same day count once (the newest one), so
    re-photographing the same damage during one visit is not treated as
    recurrence. Days are UTC days.
    """
    candidates = infrastructure.inspections.order_by("-created_at")[: window * 5]

    newest_per_day = {}
    for inspection in candidates:  # newest first, so the first one seen per day wins
        newest_per_day.setdefault(inspection.created_at.date(), inspection)

    inspections = sorted(
        newest_per_day.values(), key=lambda i: i.created_at, reverse=True
    )[:window]
    if not inspections:
        return None

    history = [
        assess(i.detections, i.image_width, i.image_height)["severity_score"]
        for i in inspections
    ]
    result = assess_health(history, infrastructure.construction_year, date.today().year)
    result["inspections_considered"] = len(history)
    return result