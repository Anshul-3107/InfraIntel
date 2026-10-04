from ml.risk.health import assess_health


def test_single_inspection_health_is_inverse_of_severity():
    r = assess_health([40])
    assert r["health_score"] == 60
    assert r["risk_level"] == "MEDIUM"
    assert r["trend"] == "insufficient history"


def test_recurrence_lowers_health():
    r = assess_health([60, 55, 70])
    assert r["health_score"] == 29
    assert r["risk_level"] == "HIGH"


def test_old_asset_gets_age_penalty():
    r = assess_health([20], construction_year=1980, current_year=2026)
    assert r["health_score"] == 70


def test_trend_worsening():
    assert assess_health([70, 40])["trend"] == "worsening"


def test_health_is_clamped_at_zero():
    r = assess_health([100] * 5, construction_year=1900, current_year=2026)
    assert r["health_score"] == 0
    assert r["risk_level"] == "CRITICAL"