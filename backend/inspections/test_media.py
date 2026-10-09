import tempfile
from unittest.mock import patch
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APITestCase
import io

from .media_access import make_token

User = get_user_model()

FAKE_RESULT = {
    "image_size": {"width": 100, "height": 100},
    "detections": [],
}


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="infraintel-private-media-"))
class ProtectedMediaTests(TestCase):
    def setUp(self):
        self.name = default_storage.save("inspections/test/a.jpg", ContentFile(b"data"))
        self.url = f"/media/{self.name}"

    def test_no_token_is_404(self):
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_valid_token_works(self):
        r = self.client.get(self.url, {"t": make_token(self.name)})
        self.assertEqual(r.status_code, 200)

    def test_token_for_another_file_is_404(self):
        r = self.client.get(self.url, {"t": make_token("inspections/test/other.jpg")})
        self.assertEqual(r.status_code, 404)

    def test_garbage_token_is_404(self):
        self.assertEqual(self.client.get(self.url, {"t": "nonsense"}).status_code, 404)

    def test_expired_token_is_404(self):
        token = make_token(self.name)
        with override_settings(MEDIA_LINK_SECONDS=-1):
            self.assertEqual(self.client.get(self.url, {"t": token}).status_code, 404)

    def test_staff_session_works_without_token(self):
        staff = User.objects.create_user("boss", password="pw-boss-1234", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_non_staff_session_without_token_is_404(self):
        user = User.objects.create_user("alice", password="pw-alice-123")
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 404)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="infraintel-private-media-"))
class ApiImageLinkTests(APITestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user("alice", password="pw-alice-123")
        r = self.client.post(
            "/api/auth/token/",
            {"username": "alice", "password": "pw-alice-123"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def test_api_returns_a_working_signed_image_link(self):
        buf = io.BytesIO()
        Image.new("RGB", (100, 100), "gray").save(buf, format="PNG")
        upload = SimpleUploadedFile("t.png", buf.getvalue(), content_type="image/png")
        with patch("inspections.views.run_detection", return_value=FAKE_RESULT):
            r = self.client.post(
                "/api/inspect/",
                {"image": upload, "latitude": 23.26, "longitude": 77.41},
                format="multipart",
            )
        self.assertEqual(r.status_code, 201)
        link = r.data["image"]
        self.assertIn("?t=", link)

        parsed = urlparse(link)
        self.client.credentials()  # the link works without any login
        ok = self.client.get(f"{parsed.path}?{parsed.query}")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(self.client.get(parsed.path).status_code, 404)