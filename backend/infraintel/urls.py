import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="dashboard-overview", permanent=False)),
    path("admin/", admin.site.urls),
    path("dashboard/", include("inspections.dashboard_urls")),
    path("api/", include("inspections.urls")),
]

# Development: Django serves uploaded images itself.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# TEMPORARY: lets the container serve photos with DEBUG off. These URLs are
# still public. The private-images step replaces this.
if not settings.DEBUG and os.getenv("SERVE_MEDIA", "0") == "1":
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        )
    ]