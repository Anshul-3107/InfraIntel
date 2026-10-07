import io
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase

from .dashboard import _display_name
from .models import Infrastructure

User = get_user_model()

FAKE_RESULT = {
    "image_size": {"width": 100, "height": 100},
    "detections": [
        {
            "damage_type": "pothole",
            "confidence": 0.8,
            "bounding_box": [10, 10, 50, 50],
            "source_model": "pothole_model",
        }
    ],
}


def png_upload():
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), "gray").save(buf, format="PNG")
    return SimpleUploadedFile("t.png", buf.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="infraintel-loc-media-"))
class LocationNameTests(APITestCase):
    def setUp(self):
        cache.clear()  # reset rate-limit counters between tests
        User.objects.create_user("alice", password="pw-alice-123")
        r = self.client.post(
            "/api/auth/token/",
            {"username": "alice", "password": "pw-alice-123"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def upload(self, location_name=None, lat=23.26, lon=77.41):
        payload = {"image": png_upload(), "latitude": lat, "longitude": lon}
        if location_name is not None:
            payload["location_name"] = location_name
        with patch("inspections.views.run_detection", return_value=FAKE_RESULT):
            return self.client.post("/api/inspect/", payload, format="multipart")

    def test_place_name_is_stored_on_inspection_and_new_asset(self):
        r = self.upload("Near Bhopal Junction, Hamidia Road")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["location_name"], "Near Bhopal Junction, Hamidia Road")
        self.assertEqual(
            r.data["infrastructure"]["location_name"],
            "Near Bhopal Junction, Hamidia Road",
        )
        asset = Infrastructure.objects.get(pk=r.data["infrastructure"]["id"])
        self.assertEqual(asset.location_name, "Near Bhopal Junction, Hamidia Road")

    def test_place_name_is_optional(self):
        r = self.upload()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["location_name"], "")

    def test_whitespace_only_name_is_treated_as_empty(self):
        r = self.upload("   ")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["location_name"], "")

    def test_too_long_name_is_rejected(self):
        r = self.upload("x" * 256)
        self.assertEqual(r.status_code, 400)

    def test_later_upload_names_an_unnamed_asset(self):
        first = self.upload()
        asset_id = first.data["infrastructure"]["id"]
        self.assertEqual(Infrastructure.objects.get(pk=asset_id).location_name, "")

        second = self.upload("Ring Road, Bhopal")
        self.assertEqual(second.data["infrastructure"]["id"], asset_id)
        self.assertEqual(
            Infrastructure.objects.get(pk=asset_id).location_name, "Ring Road, Bhopal"
        )

    def test_existing_asset_name_is_not_overwritten(self):
        first = self.upload("First name")
        second = self.upload("Second name")
        asset_id = first.data["infrastructure"]["id"]
        self.assertEqual(second.data["infrastructure"]["id"], asset_id)
        self.assertEqual(
            Infrastructure.objects.get(pk=asset_id).location_name, "First name"
        )
        # The inspection itself still records where that photo was taken.
        self.assertEqual(second.data["location_name"], "Second name")

    def test_display_name_prefers_staff_name_then_place_then_id(self):
        asset = Infrastructure.objects.create(latitude=1.0, longitude=1.0)
        self.assertEqual(_display_name(asset), f"Asset #{asset.pk}")
        asset.location_name = "Ring Road, Bhopal"
        self.assertEqual(_display_name(asset), "Ring Road, Bhopal")
        asset.name = "Custom name"
        self.assertEqual(_display_name(asset), "Custom name")