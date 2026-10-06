from django.urls import path

from . import dashboard

urlpatterns = [
    path("", dashboard.overview, name="dashboard-overview"),
    path("login/", dashboard.DashboardLoginView.as_view(), name="dashboard-login"),
    path("logout/", dashboard.DashboardLogoutView.as_view(), name="dashboard-logout"),
    path("assets/<int:pk>/", dashboard.asset_detail, name="dashboard-asset"),
    path("inspections/<int:pk>/", dashboard.inspection_detail, name="dashboard-inspection"),
    path(
        "inspections/<int:pk>/delete/",
        dashboard.inspection_delete,
        name="dashboard-inspection-delete",
    ),
    path("export/assets.csv", dashboard.export_assets, name="dashboard-export-assets"),
]