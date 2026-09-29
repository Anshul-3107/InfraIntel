from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("inspections.urls")),
]

# Serve uploaded images in development only (returns [] when DEBUG is False).
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)