"""
InfraIntel asset health engine v1 (rule-based, explainable).

Combines an asset's severity history (newest first, 0-100 per inspection) into a
0-100 health score where 100 is healthy. Like severity-v1, this is a transparent
heuristic whose weights are judgment calls, not validated against ground truth.

  effective severity = 0.6 * latest + 0.4 * mean(up to 4 earlier inspections)
  recurrence penalty = 5 per earlier inspection with severity >= 50, max 15
  age penalty        = 5 if 15+ years old, 10 if 30+ (only if year is known)
  health = 100 - effective severity - recurrence penalty - age penalty
"""

VERSION = "health-v1"
WEIGHT_LATEST = 0.6
HISTORY_WINDOW = 4
RECURRENCE_SEVERITY = 50
RECURRENCE_PENALTY_EACH = 5.0
RECURRENCE_PENALTY_MAX = 15.0
TREND_DELTA = 15

# (minimum health, risk level), checked from highest to lowest
RISK_BANDS = [(75, "LOW"), (50, "MEDIUM"), (25, "HIGH"), (0, "CRITICAL")]


def _age_penalty(age: int) -> float:
    if age >= 30:
        return 10.0
    if age >= 15:
        return 5.0
    return 0.0


def assess_health(severity_history, construction_year=None, current_year=None) -> dict:
    """severity_history: list of severity scores, newest first. Must be non-empty."""
    latest = severity_history[0]
    prior = severity_history[1 : 1 + HISTORY_WINDOW]

    if prior:
        prior_mean = sum(prior) / len(prior)
        effective = WEIGHT_LATEST * latest + (1 - WEIGHT_LATEST) * prior_mean
    else:
        prior_mean = None
        effective = float(latest)

    severe_prior = sum(1 for s in prior if s >= RECURRENCE_SEVERITY)
    recurrence = min(RECURRENCE_PENALTY_MAX, RECURRENCE_PENALTY_EACH * severe_prior)

    age = None
    age_penalty = 0.0
    if construction_year and current_year:
        age = max(0, current_year - construction_year)
        age_penalty = _age_penalty(age)

    health = int(round(max(0.0, min(100.0, 100.0 - effective - recurrence - age_penalty))))
    risk_level = next(level for floor, level in RISK_BANDS if health >= floor)

    if not prior:
        trend = "insufficient history"
    elif latest - prior[0] >= TREND_DELTA:
        trend = "worsening"
    elif prior[0] - latest >= TREND_DELTA:
        trend = "improving"
    else:
        trend = "stable"

    reasons = [f"Latest inspection severity {latest}/100"]
    if prior:
        reasons.append(f"Average severity of {len(prior)} earlier inspection(s): {prior_mean:.0f}/100")
    if severe_prior:
        reasons.append(f"{severe_prior} earlier inspection(s) were already severe (>= {RECURRENCE_SEVERITY})")
    if trend == "worsening":
        reasons.append("Condition is worsening compared with the previous inspection")
    elif trend == "improving":
        reasons.append(
            "Condition looks better than the previous inspection "
            "(may reflect a repair or a different photo angle)"
        )
    if age_penalty:
        reasons.append(f"Asset is {age} years old")
    if construction_year is None:
        reasons.append("Construction year unknown; age not factored in")

    return {
        "version": VERSION,
        "health_score": health,
        "risk_level": risk_level,
        "trend": trend,
        "reasons": reasons,
    }