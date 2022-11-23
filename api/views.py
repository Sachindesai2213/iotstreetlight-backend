from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import *
from .methods import log_activity, meters_data
from datetime import datetime
import json

# Create your views here.
@api_view(['POST'])
def user_view(request):
    if request.method == 'POST':
        return Response()


@api_view(['POST'])
@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        username = request.data['username']
        password = request.data['password']
        username_exists = User.objects.filter(Q(username=username) | Q(email=username)).last()
        data = {
            'flash': False,
            'message': 'Invalid Username',
            'data': {
                'username': '',
                'user_id': ''
            }
        }
        if username_exists:
            user = authenticate(request, username=username_exists.username, password=password)
            data['flash'] = True if user else False
            data['message'] = 'Successful' if user else 'Password Incorrect'
            data['data']['username'] = user.username if user else None
            data['data']['user_id'] = user.id if user else None
        if data['data']['user_id']:
            log_activity(user.id, 'Login Successful')
        else:
            log_activity(user.id, 'Login Unsuccessful - ' + data['message'])
        return Response(data)


@api_view(['POST'])
@csrf_exempt
def signup_view(request):
    if request.method == 'POST':
        username = request.data['username']
        password = request.data['password']
        email = request.data['email']
        first_name = request.data['first_name']
        last_name = request.data['last_name']
        contact_no = request.data['contact_no']
        user = User.objects.filter(Q(username=username) | Q(email=email)).last()
        data = {
            'flash': False,
            'message': 'Username/Email exists',
            'data': {}
        }
        if not user:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            user_data = UserInfo(
                user=user,
                contact=contact_no
            )
            user_data.save()
            data['flash'] = True
            data['message'] = 'Successful'
            data['data']['user_id'] = user.id
            data['data']['username'] = user.username
            log_activity(user.id, 'Signup Successful')
        return Response(data)


@api_view(['POST', 'GET'])
@csrf_exempt
def meters_view(request):
    if request.method == 'POST':
        meter_name = request.data['meter_name']
        poles_r = request.data['poles_r']
        poles_y = request.data['poles_y']
        poles_b = request.data['poles_b']
        group = request.data['group']
        period_type = request.data['period_type']
        lat = request.data['lat']
        lon = request.data['lon']
        sunrise_offset = request.data['sunrise_offset']
        sunset_offset = request.data['sunset_offset']
        on_time = request.data['on_time']
        off_time = request.data['off_time']
        user_id = request.data['user_id']
        meter = Meter(
            meter_name = meter_name,
            poles_r = poles_r,
            poles_y = poles_y,
            poles_b = poles_b,
            group = group,
            period_type = period_type,
            lat = lat,
            lon = lon,
            sunrise_offset = sunrise_offset,
            sunset_offset = sunset_offset,
            on_time = on_time,
            off_time = off_time,
            created_by_id = user_id
        )
        meter.save()
        log_activity(user_id, 'Added Meter ID#' + str(meter.id))
        meters = meters_data(user_id)
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {
                'meters': meters
            }
        }
        return Response(data)
    elif request.method == 'GET':
        user_id = request.query_params['user_id']
        meters = meters_data(user_id)
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {
                'meters': meters
            }
        }  
        return Response(data)


@api_view(['POST'])
@csrf_exempt
def meter_parameters_view(request):
    if request.method == 'POST':
        meter_id = request.data['meter_id']
        parameter_name = request.data['parameter_name']
        field_name = request.data['field_name']
        min_thr = request.data['min_thr']
        max_thr = request.data['max_thr']
        user_id = request.data['user_id']
        notify = request.data['notify']
        meter_parameter = MetersThreshold(
            meter_id = meter_id,
            parameter_name = parameter_name,
            field_name = field_name,
            min_thr = min_thr,
            max_thr = max_thr,
            notify = True if notify == 'Yes' else False,
            created_by_id = user_id
        )
        meter_parameter.save()
        log_activity(user_id, 'Added Meter Parameter ID#' + str(meter_parameter.id))
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {}
        }  
        return Response(data)


@api_view(['GET'])
@csrf_exempt
def activities_view(request):
    if request.method == 'GET':
        user_id = request.query_params['user_id']
        activities = list(ActivityLog.objects.filter(user_id=user_id).values('user_id', 'user__first_name', 'user__last_name', 'type', 'timestamp', 'seen'))
        for activity in activities:
            activity['timestamp'] = activity['timestamp'].strftime('%d-%m-%Y %H:%M:%S')
            activity['seen'] = 'Yes' if activity['seen'] else 'No'
            activity['name'] = activity['user__first_name'] + ' ' + activity['user__last_name']
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {
                'activities': activities
            }
        }
        return Response(data)


@api_view(['GET'])
@csrf_exempt
def analytics_view(request):
    if request.method == 'GET':
        user_id = request.query_params['user_id']
        start_date = datetime.strptime(request.query_params['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.query_params['end_date'], '%Y-%m-%d').date()
        reports = list(MeterData.objects.filter(inserted_on__date__range=(start_date, end_date), meter__created_by_id=user_id).values('meter_id', 'meter__meter_name', 'v_r', 'v_y', 'v_b', 'c_r', 'c_y', 'c_b', 'p_r', 'p_y', 'p_b', 'pf', 'kvar', 'freq', 'kwh', 'kvah', 'inserted_on')) 
        for report in reports:
            report['inserted_on'] = report['inserted_on'].strftime('%d-%m-%Y %H:%M:%S')
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {
                'reports': reports
            }
        }
        return Response(data)
