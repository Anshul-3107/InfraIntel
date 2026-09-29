from django.urls import path

from .views import InspectView

urlpatterns = [
    path("inspect/", InspectView.as_view(), name="inspect"),
]