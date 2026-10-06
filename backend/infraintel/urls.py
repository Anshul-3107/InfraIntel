from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="dashboard-overview", permanent=False)),
    path("admin/", admin.site.urls),
    path("dashboard/", include("inspections.dashboard_urls")),
    path("api/", include("inspections.urls")),
]

# Serve uploaded images in development only (returns [] when DEBUG is False).
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)