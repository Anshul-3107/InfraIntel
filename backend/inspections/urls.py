from django.urls import path

from .views import (
    InfrastructureDetailView,
    InfrastructureListView,
    InspectionDetailView,
    InspectionListView,
    InspectView,
)

urlpatterns = [
    path("inspect/", InspectView.as_view(), name="inspect"),
    path("inspections/", InspectionListView.as_view(), name="inspection-list"),
    path("inspections/<int:pk>/", InspectionDetailView.as_view(), name="inspection-detail"),
    path("infrastructure/", InfrastructureListView.as_view(), name="infrastructure-list"),
    path("infrastructure/<int:pk>/", InfrastructureDetailView.as_view(), name="infrastructure-detail"),
]