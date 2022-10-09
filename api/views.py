from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import *
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
        return Response(data)


@api_view(['POST'])
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
        parameters = json.loads(request.data['parameters'])
        for parameter in parameters:
            meter_parameter = MetersThreshold(
                meter = meter,
                parameter_name = parameter['parameter_name'],
                field_name = parameter['field_name'],
                unit = parameter['unit'],
                min_thr = parameter['min_thr'],
                max_thr = parameter['max_thr'],
                notify = parameter['notify'],
                created_by_id = user_id
            )
            meter_parameter.save()
        return Response()
    elif request.method == 'GET':
        user_id = request.query_params['user_id']
        meters = list(Meter.objects.filter(created_by_id=user_id).values())
        for meter in meters:
            meter['parameters'] = list(MetersThreshold.objects.filter(meter_id=meter['id']).values())
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {
                'meters': meters
            }
        }  
        return Response(data)