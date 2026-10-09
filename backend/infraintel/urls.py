from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView

from inspections.media_access import protected_media

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="dashboard-overview", permanent=False)),
    path("admin/", admin.site.urls),
    path("dashboard/", include("inspections.dashboard_urls")),
    path("api/", include("inspections.urls")),
    # Photos are private: signed link or staff login required (also in DEBUG).
    re_path(r"^media/(?P<path>.+)$", protected_media, name="protected-media"),
]