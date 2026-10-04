"""
InfraIntel severity engine v1 (rule-based, explainable).

Turns raw detections into a 0-100 severity score, a priority band, and a list of
human-readable reasons. This is a transparent heuristic, not a trained model:
the weights below are judgment calls, not validated against ground truth.

How the score works:
  1. Detections below MIN_CONFIDENCE are ignored (and reported).
  2. For each damage type, overlapping boxes are merged so area is not double
     counted, giving the fraction of the frame that type covers.
  3. Each type earns points up to its maximum, saturating once its coverage
     reaches that type's saturation fraction.
  4. Multiple potholes add a small bonus.
  5. Total is capped at 100 and mapped to a priority band.

Usage:
    from ml.risk.severity import assess
    result = assess(detections, image_width, image_height)
"""

import numpy as np

VERSION = "severity-v1"
MIN_CONFIDENCE = 0.30
GRID = 400  # coverage is measured on a GRID x GRID mask of the frame

# damage type -> (max points, coverage fraction of frame at which points saturate)
DAMAGE_PROFILE = {
    "pothole": (45.0, 0.10),
    "alligator_crack": (40.0, 0.40),
    "longitudinal_crack": (15.0, 0.15),
    "transverse_crack": (15.0, 0.15),
}
POTHOLE_BONUS_EACH = 3.0
POTHOLE_BONUS_MAX = 12.0

# (minimum score, label), checked from highest to lowest
PRIORITY_BANDS = [(75, "CRITICAL"), (50, "HIGH"), (25, "MEDIUM"), (0, "LOW")]

LABELS = {
    "pothole": "pothole",
    "alligator_crack": "alligator crack",
    "longitudinal_crack": "longitudinal crack",
    "transverse_crack": "transverse crack",
}


def _union_coverage(boxes, width, height) -> float:
    """Fraction of the frame covered by the union of boxes (xmin, ymin, xmax, ymax)."""
    if not boxes or width <= 0 or height <= 0:
        return 0.0
    mask = np.zeros((GRID, GRID), dtype=bool)
    for x1, y1, x2, y2 in boxes:
        gx1 = int(round(max(0.0, x1) / width * GRID))
        gx2 = int(round(min(float(width), x2) / width * GRID))
        gy1 = int(round(max(0.0, y1) / height * GRID))
        gy2 = int(round(min(float(height), y2) / height * GRID))
        if gx2 <= gx1:
            gx2 = gx1 + 1
        if gy2 <= gy1:
            gy2 = gy1 + 1
        mask[gy1:gy2, gx1:gx2] = True
    return float(mask.mean())


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _describe(damage_type: str, count: int, coverage: float) -> str:
    pct = coverage * 100
    label = LABELS[damage_type]
    if damage_type == "pothole":
        return f"{_plural(count, 'pothole')} covering {pct:.1f}% of the frame"
    if damage_type == "alligator_crack":
        return f"Alligator cracking over {pct:.0f}% of the frame ({_plural(count, 'region')})"
    return f"{_plural(count, label)} covering {pct:.1f}% of the frame"


def assess(detections, image_width, image_height, min_confidence=MIN_CONFIDENCE) -> dict:
    ignored_low_conf = sum(1 for d in detections if d.get("confidence", 0) < min_confidence)
    kept = [
        d for d in detections
        if d.get("confidence", 0) >= min_confidence and d.get("damage_type") in DAMAGE_PROFILE
    ]

    boxes_by_type = {}
    for d in kept:
        boxes_by_type.setdefault(d["damage_type"], []).append(d["bounding_box"])

    coverage, points = {}, {}
    for damage_type, boxes in boxes_by_type.items():
        cov = _union_coverage(boxes, image_width, image_height)
        max_points, saturation = DAMAGE_PROFILE[damage_type]
        coverage[damage_type] = cov
        points[damage_type] = max_points * min(cov / saturation, 1.0)

    n_potholes = len(boxes_by_type.get("pothole", []))
    bonus = min(POTHOLE_BONUS_MAX, POTHOLE_BONUS_EACH * max(0, n_potholes - 1))

    total = min(100.0, sum(points.values()) + bonus)
    score = int(round(total))
    priority = next(label for floor, label in PRIORITY_BANDS if score >= floor)

    reasons = []
    if not kept:
        reasons.append("No damage detected above the confidence threshold")
    for damage_type in sorted(points, key=points.get, reverse=True):
        reasons.append(_describe(damage_type, len(boxes_by_type[damage_type]), coverage[damage_type]))
    if n_potholes >= 3:
        reasons.append(f"Multiple potholes ({n_potholes}) raise the score")
    if ignored_low_conf:
        reasons.append(f"{_plural(ignored_low_conf, 'low-confidence detection')} ignored")

    breakdown = {t: round(p, 1) for t, p in points.items()}
    breakdown["pothole_count_bonus"] = round(bonus, 1)

    return {
        "version": VERSION,
        "severity_score": score,
        "priority": priority,
        "coverage_pct": {t: round(c * 100, 2) for t, c in coverage.items()},
        "score_breakdown": breakdown,
        "reasons": reasons,
        "ignored_low_confidence": ignored_low_conf,
    }