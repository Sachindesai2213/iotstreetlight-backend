from django.urls import path
from .views import login_view, signup_view, profile_view, dashboard_data_view, meters_view, meter_parameters_view, activities_view, reports_view, hourly_report_view, daily_report_view, monthly_report_view

urlpatterns = [
    path('login', login_view, name='login'),
    path('signup', signup_view, name='signup'),
    path('profile', profile_view, name='profile'),
    path('dashboard-data', dashboard_data_view, name='dashboard-data'),
    path('meters', meters_view, name='meters'),
    path('meter-parameters', meter_parameters_view, name='meters-parameters'),
    path('activities', activities_view, name='activities'),
    path('reports', reports_view, name='reports'),
    path('hourly-report', hourly_report_view, name='hourly-report'),
    path('daily-report', daily_report_view, name='daily-report'),
    path('monthly-report', monthly_report_view, name='monthly-report'),
]