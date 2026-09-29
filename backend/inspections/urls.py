from django.urls import path

from .views import InspectionDetailView, InspectView

urlpatterns = [
    path("inspect/", InspectView.as_view(), name="inspect"),
    path("inspections/<int:pk>/", InspectionDetailView.as_view(), name="inspection-detail"),
]