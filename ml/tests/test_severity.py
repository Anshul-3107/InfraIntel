from ml.risk.severity import assess

W = H = 1000


def det(damage_type, conf, box):
    return {"damage_type": damage_type, "confidence": conf,
            "bounding_box": list(box), "source_model": "test"}


def test_no_detections_is_low():
    r = assess([], W, H)
    assert r["severity_score"] == 0
    assert r["priority"] == "LOW"
    assert r["reasons"]


def test_low_confidence_is_ignored():
    r = assess([det("pothole", 0.20, (0, 0, 500, 500))], W, H)
    assert r["severity_score"] == 0
    assert r["ignored_low_confidence"] == 1


def test_full_frame_alligator_is_medium():
    r = assess([det("alligator_crack", 0.9, (0, 0, 1000, 1000))], W, H)
    assert r["severity_score"] == 40
    assert r["priority"] == "MEDIUM"


def test_overlapping_boxes_not_double_counted():
    boxes = [det("alligator_crack", 0.9, (0, 0, 1000, 200))] * 2
    r = assess(boxes, W, H)
    assert r["coverage_pct"]["alligator_crack"] == 20.0
    assert r["score_breakdown"]["alligator_crack"] == 20.0


def test_multiple_potholes_get_bonus():
    potholes = [det("pothole", 0.8, (x, 0, x + 100, 100)) for x in (0, 200, 400)]
    r = assess(potholes, W, H)
    assert r["score_breakdown"]["pothole_count_bonus"] == 6.0
    assert any("Multiple potholes" in reason for reason in r["reasons"])


def test_score_is_capped_at_100():
    full = (0, 0, 1000, 1000)
    dets = [det(t, 0.9, full) for t in
            ("pothole", "alligator_crack", "longitudinal_crack", "transverse_crack")]
    r = assess(dets, W, H)
    assert r["severity_score"] == 100
    assert r["priority"] == "CRITICAL"