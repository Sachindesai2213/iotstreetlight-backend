from django.urls import path
from .views import login_view, signup_view, meters_view, meter_parameters_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('meters/', meters_view, name='meters'),
    path('meter-parameters/', meter_parameters_view, name='meters-parameters'),
]