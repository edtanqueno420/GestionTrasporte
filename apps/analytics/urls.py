from django.urls import include, path

from apps.analytics.views import DashboardView, RouteReportView, SystemStatusView, VehicleReportView

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="analytics-dashboard"),
    path("routes/<int:pk>/report/", RouteReportView.as_view(), name="analytics-route-report"),
    path("vehicles/<int:pk>/report/", VehicleReportView.as_view(), name="analytics-vehicle-report"),
    path("status/", SystemStatusView.as_view(), name="analytics-status"),
]
