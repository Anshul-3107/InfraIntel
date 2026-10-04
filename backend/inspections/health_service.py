from datetime import date

from ml.risk.health import assess_health
from ml.risk.severity import assess


def asset_health(infrastructure, window: int = 10):
    """Health for an asset from its most recent inspections, or None if it has none."""
    inspections = list(infrastructure.inspections.order_by("-created_at")[:window])
    if not inspections:
        return None
    history = [
        assess(i.detections, i.image_width, i.image_height)["severity_score"]
        for i in inspections
    ]
    result = assess_health(history, infrastructure.construction_year, date.today().year)
    result["inspections_considered"] = len(history)
    return result