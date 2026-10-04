from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    InfrastructureDetailView,
    InfrastructureListView,
    InspectionDetailView,
    InspectionListView,
    InspectView,
    MeView,
    ThrottledTokenObtainPairView,
)

urlpatterns = [
    path("auth/token/", ThrottledTokenObtainPairView.as_view(), name="token"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("inspect/", InspectView.as_view(), name="inspect"),
    path("inspections/", InspectionListView.as_view(), name="inspection-list"),
    path("inspections/<int:pk>/", InspectionDetailView.as_view(), name="inspection-detail"),
    path("infrastructure/", InfrastructureListView.as_view(), name="infrastructure-list"),
    path("infrastructure/<int:pk>/", InfrastructureDetailView.as_view(), name="infrastructure-detail"),
]