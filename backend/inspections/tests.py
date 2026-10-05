import io
import os
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase

from .models import Infrastructure, Inspection

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


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="infraintel-test-media-"))
class AuthAndVisibilityTests(APITestCase):
    def setUp(self):
        cache.clear()  # reset rate-limit counters between tests
        self.alice = User.objects.create_user("alice", password="pw-alice-123")
        self.bob = User.objects.create_user("bob", password="pw-bob-12345")
        self.boss = User.objects.create_user(
            "boss", password="pw-boss-1234", is_staff=True
        )

    def login(self, username, password):
        r = self.client.post(
            "/api/auth/token/",
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def upload(self, lat=23.26, lon=77.41):
        with patch("inspections.views.run_detection", return_value=FAKE_RESULT):
            return self.client.post(
                "/api/inspect/",
                {"image": png_upload(), "latitude": lat, "longitude": lon},
                format="multipart",
            )

    def test_requests_without_token_are_rejected(self):
        self.assertEqual(self.client.get("/api/inspections/").status_code, 401)
        self.assertEqual(self.upload().status_code, 401)

    def test_bad_password_is_rejected(self):
        r = self.client.post(
            "/api/auth/token/",
            {"username": "alice", "password": "wrong"},
            format="json",
        )
        self.assertEqual(r.status_code, 401)

    def test_upload_records_inspector(self):
        self.login("alice", "pw-alice-123")
        r = self.upload()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["inspector"], "alice")

    def test_inspector_sees_only_own_inspections(self):
        self.login("alice", "pw-alice-123")
        self.upload()
        self.login("bob", "pw-bob-12345")
        self.assertEqual(self.client.get("/api/inspections/").data["count"], 0)

    def test_inspector_cannot_open_anothers_inspection(self):
        self.login("alice", "pw-alice-123")
        inspection_id = self.upload().data["id"]
        self.login("bob", "pw-bob-12345")
        r = self.client.get(f"/api/inspections/{inspection_id}/")
        self.assertEqual(r.status_code, 404)

    def test_staff_sees_everything(self):
        self.login("alice", "pw-alice-123")
        self.upload()
        self.login("boss", "pw-boss-1234")
        self.assertEqual(self.client.get("/api/inspections/").data["count"], 1)
        self.assertEqual(self.client.get("/api/auth/me/").data["role"], "staff")

    def test_nearby_uploads_share_one_asset_and_far_one_does_not(self):
        self.login("alice", "pw-alice-123")
        first = self.upload(23.2599, 77.4126).data["infrastructure"]["id"]
        second = self.upload(23.25995, 77.41262).data["infrastructure"]["id"]
        far = self.upload(23.2699, 77.4126).data["infrastructure"]["id"]
        self.assertEqual(first, second)
        self.assertNotEqual(first, far)

    def test_detection_failure_returns_422(self):
        self.login("alice", "pw-alice-123")
        with patch("inspections.views.run_detection", side_effect=RuntimeError("boom")):
            r = self.client.post(
                "/api/inspect/",
                {"image": png_upload(), "latitude": 23.26, "longitude": 77.41},
                format="multipart",
            )
        self.assertEqual(r.status_code, 422)

    # ---- deleting inspections -------------------------------------------

    def test_delete_requires_login(self):
        self.login("alice", "pw-alice-123")
        inspection_id = self.upload().data["id"]
        self.client.credentials()  # drop the token
        r = self.client.delete(f"/api/inspections/{inspection_id}/")
        self.assertEqual(r.status_code, 401)
        self.assertTrue(Inspection.objects.filter(pk=inspection_id).exists())

    def test_owner_can_delete_and_image_file_is_removed(self):
        self.login("alice", "pw-alice-123")
        inspection_id = self.upload().data["id"]
        path = Inspection.objects.get(pk=inspection_id).image.path
        self.assertTrue(os.path.exists(path))

        r = self.client.delete(f"/api/inspections/{inspection_id}/")

        self.assertEqual(r.status_code, 204)
        self.assertFalse(Inspection.objects.filter(pk=inspection_id).exists())
        self.assertFalse(os.path.exists(path))
        self.assertEqual(
            self.client.get(f"/api/inspections/{inspection_id}/").status_code, 404
        )

    def test_other_inspector_cannot_delete(self):
        self.login("alice", "pw-alice-123")
        inspection_id = self.upload().data["id"]
        self.login("bob", "pw-bob-12345")
        r = self.client.delete(f"/api/inspections/{inspection_id}/")
        self.assertEqual(r.status_code, 404)
        self.assertTrue(Inspection.objects.filter(pk=inspection_id).exists())

    def test_staff_can_delete_any_inspection(self):
        self.login("alice", "pw-alice-123")
        inspection_id = self.upload().data["id"]
        self.login("boss", "pw-boss-1234")
        r = self.client.delete(f"/api/inspections/{inspection_id}/")
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Inspection.objects.filter(pk=inspection_id).exists())

    def test_auto_created_asset_is_removed_with_its_last_inspection(self):
        self.login("alice", "pw-alice-123")
        inspection_id = self.upload().data["id"]
        self.assertEqual(Infrastructure.objects.count(), 1)
        self.client.delete(f"/api/inspections/{inspection_id}/")
        self.assertEqual(Infrastructure.objects.count(), 0)

    def test_asset_is_kept_while_other_inspections_remain(self):
        self.login("alice", "pw-alice-123")
        first = self.upload().data
        second = self.upload().data
        asset_id = first["infrastructure"]["id"]
        self.assertEqual(asset_id, second["infrastructure"]["id"])

        self.client.delete(f"/api/inspections/{first['id']}/")
        self.assertTrue(Infrastructure.objects.filter(pk=asset_id).exists())

        self.client.delete(f"/api/inspections/{second['id']}/")
        self.assertFalse(Infrastructure.objects.filter(pk=asset_id).exists())

    def test_named_asset_survives_deleting_its_last_inspection(self):
        asset = Infrastructure.objects.create(
            name="Bypass road", latitude=23.26, longitude=77.41
        )
        self.login("alice", "pw-alice-123")
        inspection_id = self.upload(23.26, 77.41).data["id"]
        self.assertEqual(
            Inspection.objects.get(pk=inspection_id).infrastructure_id, asset.pk
        )
        self.client.delete(f"/api/inspections/{inspection_id}/")
        self.assertTrue(Infrastructure.objects.filter(pk=asset.pk).exists())