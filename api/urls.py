from django.urls import path
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .views import (ActivitiesView, DeviceConfigurationsView,
                    DeviceParametersView, DevicesView, DeviceView, FaultsView,
                    UsersView, UserView, dashboard_data_view,
                    interval_report_view, reports_view)

urlpatterns = [
    path('token', TokenObtainPairView.as_view(),
         name='token-obtain-pair'),
    path('token/refresh', TokenRefreshView.as_view(),
         name='token-refresh'),
    path('users', UsersView.as_view(), name='users'),
    path('user/<int:id>', UserView.as_view(), name='user'),
    path('dashboard-data', dashboard_data_view, name='dashboard-data'),
    path('devices', DevicesView.as_view(), name='devices'),
    path('device/<int:id>', DeviceView.as_view(), name='device'),
    path('device-parameters', DeviceParametersView.as_view(),
         name='devices-parameters'),
    path('device-configurations', DeviceConfigurationsView.as_view(),
         name='devices-configurations'),
    path('activities', ActivitiesView.as_view(), name='activities'),
    path('reports', reports_view, name='reports'),
    path('interval-report', interval_report_view, name='interval-report'),
    path('faults', FaultsView.as_view(), name='faults'),
]
