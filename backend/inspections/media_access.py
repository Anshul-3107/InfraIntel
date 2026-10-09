"""Private access to uploaded inspection photos.

A photo can be opened in two ways:
  * with a signed, expiring link (the API puts one in every response), or
  * by a signed-in staff member (the dashboard).
Everything else gets a 404, so the response does not reveal that a file exists.
"""

from django.conf import settings
from django.core import signing
from django.http import Http404
from django.views.decorators.http import require_safe
from django.views.static import serve

SALT = "inspections.media"


def make_token(path: str) -> str:
    return signing.dumps(path, salt=SALT)


def signed_media_url(path: str) -> str:
    """Relative URL for a stored file, with a signed token attached."""
    return f"{settings.MEDIA_URL}{path}?t={make_token(path)}"


def _token_allows(token: str, path: str) -> bool:
    if not token:
        return False
    try:
        signed_path = signing.loads(
            token,
            salt=SALT,
            max_age=getattr(settings, "MEDIA_LINK_SECONDS", 3600),
        )
    except signing.BadSignature:  # includes SignatureExpired
        return False
    return signed_path == path


@require_safe
def protected_media(request, path):
    user = request.user
    staff = user.is_authenticated and user.is_active and user.is_staff
    if not staff and not _token_allows(request.GET.get("t", ""), path):
        raise Http404
    # serve() refuses paths that try to escape MEDIA_ROOT.
    response = serve(request, path, document_root=settings.MEDIA_ROOT)
    response["Cache-Control"] = "private, max-age=300"
    return response