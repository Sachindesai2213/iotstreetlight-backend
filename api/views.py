from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F, Q, Avg, Sum
from .models import *
from .methods import log_activity, devices_data
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
import json
import os
from backend.mqtt import on_publish, on_disconnect


# Create your views here.
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
            data['data']['devices'] = list(Device.objects.annotate(value=F('id')).filter(created_by_id=user.id).values('id', 'name', 'value'))
            for device in data['data']['devices']:
                device['parameters'] = list(DeviceParameter.objects.annotate(value=F('key')).filter(device_id=device['id']).values('id', 'name', 'value'))
        else:
            log_activity(user.id, 'Login Unsuccessful - ' + data['message'])
        return Response(data)


@api_view(['GET', 'POST'])
def profile_view(request):
    if request.method == 'GET':
        user_id = request.query_params['user_id']
        user = User.objects.get(id=user_id)
        user_info = UserInfo.objects.get(id=user_id)
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'contact_no': user_info.contact
            }
        }
        return Response(data)
    elif request.method == 'POST':
        user_id = request.data['user_id']
        user = User.objects.get(id=user_id)
        user.first_name = request.data['first_name']
        user.last_name = request.data['last_name']
        user.email = request.data['email']
        user.save(update_fields=['first_name', 'last_name', 'email'])
        user_info = UserInfo.objects.get(id=user_id)
        user_info.contact = request.data['contact']
        user_info.save(update_fields=['contact'])
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'contact_no': user_info.contact
            }
        }
        return Response(data)


@api_view(['GET'])
@csrf_exempt
def dashboard_data_view(request):
    if request.method == 'GET':
        user_id = request.query_params['user_id']
        current_date = datetime.now().date()
        devices = Device.objects.filter(created_by_id=user_id).count()
        faults = Faults.objects.filter(device__created_by_id=user_id).count()
        power_consumption_today = DeviceData.objects.filter(log__inserted_on__date=current_date, parameter__device__created_by_id=user_id, parameter__name__contains='Power').aggregate(Sum('value'))
        power_consumption_current_month = DeviceData.objects.filter(log__inserted_on__month=current_date.month, log__inserted_on__year=current_date.year, parameter__device__created_by_id=user_id, parameter__name__contains='Power').aggregate(Sum('value'))
        data = {
            'flash': True,
            'message': 'Successful',
            'data': [
                {
                    'title': "POWER - TODAY",
                    'value': power_consumption_today['value__sum'] if power_consumption_today['value__sum'] else 'N/A',
                    'isIncreased': True,
                    'percentage': 0,
                    'icon': "usage",
                    'link': "/reports"
                },
                {
                    'title': "POWER - CURRENT MONTH",
                    'value': power_consumption_current_month['value__sum'] if power_consumption_current_month['value__sum'] else 'N/A',
                    'isIncreased': True,
                    'percentage': 0,
                    'icon': "power",
                    'link': "/reports"
                },
                {
                    'title': 'Devices',
                    'value': devices,
                    'isIncreased': True,
                    'percentage': 0,
                    'icon': "meters",
                    'link': "/devices"
                },
                {
                    'title': 'FAULTS',
                    'value': faults,
                    'isIncreased': True,
                    'percentage': 0,
                    'icon': "faults",
                    'link': "/faults"
                },
            ]
        }
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
def devices_view(request):
    if request.method == 'POST':
        name = request.data['name']
        group = request.data['group']
        period_type = request.data['period_type']
        lat = request.data['lat']
        lon = request.data['lon']
        sunrise_offset = request.data['sunrise_offset']
        sunset_offset = request.data['sunset_offset']
        on_time = request.data['on_time']
        off_time = request.data['off_time']
        user_id = request.data['user_id']
        device = Device(
            name = name,
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
        device.save()
        log_activity(user_id, 'Added Device ID#' + str(device.id))
        devices = devices_data(user_id)
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {
                'devices': devices
            }
        }
        return Response(data)
    elif request.method == 'GET':
        user_id = request.query_params['user_id']
        devices = devices_data(user_id)
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {
                'devices': devices
            }
        }  
        return Response(data)


@api_view(['POST'])
@csrf_exempt
def device_parameters_view(request):
    if request.method == 'POST':
        device_id = request.data['device_id']
        name = request.data['name']
        key = request.data['key']
        min_thr = request.data['min_thr']
        max_thr = request.data['max_thr']
        user_id = request.data['user_id']
        notify = request.data['notify']
        device_parameter = DeviceParameter(
            device_id = device_id,
            name = name,
            key = key,
            min_thr = min_thr,
            max_thr = max_thr,
            notify = True if notify == 'Yes' else False,
            created_by_id = user_id
        )
        device_parameter.save()
        log_activity(user_id, 'Added Device Parameter ID#' + str(device_parameter.id))
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {}
        }  
        return Response(data)


@api_view(['POST', 'PUT'])
@csrf_exempt
def device_configurations_view(request):
    if request.method == 'POST':
        device_id = request.data['device_id']
        name = request.data['name']
        key = request.data['key']
        value = request.data['value']
        user_id = request.data['user_id']
        device_configuration = DeviceConfiguration(
            device_id = device_id,
            name = name,
            key = key,
            value = value,
            created_by_id = user_id
        )
        device_configuration.save()
        log_activity(user_id, 'Added Device Configuration ID#' + str(device_configuration.id))
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {}
        }  
        return Response(data)
    elif request.method == 'PUT':
        configurations = list(DeviceConfiguration.objects.filter(device_id=request.data['id']).values('id', 'device_id', 'device__name', 'name', 'key', 'value'))
        data = json.dumps(configurations)
        client_push = mqtt.Client()
        client_push.username_pw_set(username='sachin3913', password=os.environ.get('ADAFRUIT_KEY'))
        client_push.on_publish = on_publish
        client_push.on_disconnect = on_disconnect
        client_push.connect("io.adafruit.com", 1883)
        client_push.publish('sachin3913/feeds/python', data.encode('utf-8'), qos=0)
        client_push.disconnect()
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
def reports_view(request):
    if request.method == 'GET':
        device_id = request.query_params['device_id']
        start_date = datetime.strptime(request.query_params['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.query_params['end_date'], '%Y-%m-%d').date()
        parameters = list(DeviceParameter.objects.filter(device_id=device_id).values('key', 'name'))
        device_data_logs = list(DeviceDataLog.objects.filter(inserted_on__date__range=(start_date, end_date), 
        device_id=device_id).values('id', 'device_id', 'device__name', 'inserted_on'))
        for log in device_data_logs:
            log['inserted_on'] = log['inserted_on'].strftime('%d-%m-%Y %H:%M:%S')
            device_data = dict(DeviceData.objects.filter(log_id=log['id']).values_list('parameter__key', 'value'))
            for parameter in parameters:
                log[parameter['key']] = device_data[parameter['key']] if parameter['key'] in device_data else ''
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {
                'reports': device_data_logs,
                'parameters': parameters
            }
        }
        return Response(data)


@api_view(['GET'])
@csrf_exempt
def hourly_report_view(request):
    if request.method == 'GET':
        device_id = request.query_params['device_id']
        parameter_1 = request.query_params['parameter_1']
        parameter_2 = request.query_params['parameter_2']
        type = request.query_params['type']
        date = datetime.strptime(request.query_params['date'], '%Y-%m-%d')
        start_datetime = date.replace(hour=0, minute=0, second=1)
        end_datetime = date.replace(hour=1, minute=0, second=0)
        hours = []
        parameter_1_report_data = []
        parameter_2_report_data = []
        while date.date() == start_datetime.date():
            hours.append(str(start_datetime.hour))
            parameter_1_data = DeviceData.objects.filter(log__inserted_on__range=(start_datetime, end_datetime), parameter__device_id=device_id, parameter__key=parameter_1)
            parameter_1_data = parameter_1_data.aggregate(Avg('value')) if type == 'avg' else parameter_1_data.aggregate(Sum('value'))
            parameter_1_data = parameter_1_data['value__' + type] if parameter_1_data['value__' + type] else 0
            parameter_1_report_data.append(parameter_1_data)
            if parameter_2:
                parameter_2_data = DeviceData.objects.filter(log__inserted_on__range=(start_datetime, end_datetime), parameter__device_id=device_id, parameter__key=parameter_2)
                parameter_2_data = parameter_2_data.aggregate(Avg('value')) if type == 'avg' else parameter_2_data.aggregate(Sum('value'))
                parameter_2_data = parameter_2_data['value__' + type] if parameter_2_data['value__' + type] else 0
                parameter_2_report_data.append(parameter_2_data)
            start_datetime += timedelta(hours=1)
            end_datetime += timedelta(hours=1)
        datasets = [
            {'label': parameter_1, 'data': parameter_1_report_data}
        ]
        if parameter_2_report_data:
            datasets.append({'label': parameter_2, 'data': parameter_2_report_data})
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {
                'labels': hours,
                'datasets': datasets,
            }
        }
        return Response(data)


@api_view(['GET'])
@csrf_exempt
def daily_report_view(request):
    if request.method == 'GET':
        device_id = request.query_params['device_id']
        parameter_1 = request.query_params['parameter_1']
        parameter_2 = request.query_params['parameter_2']
        type = request.query_params['type']
        start_date = datetime.strptime(request.query_params['month'] + '-01', '%Y-%m-%d').date()
        end_date = start_date
        days = []
        parameter_1_report_data = []
        parameter_2_report_data = []
        while start_date.month == end_date.month:
            days.append(str(end_date.day))
            parameter_1_data = DeviceData.objects.filter(log__inserted_on__date=end_date, parameter__device_id=device_id, parameter__key=parameter_1)
            parameter_1_data = parameter_1_data.aggregate(Avg('value')) if type == 'avg' else parameter_1_data.aggregate(Sum('value'))
            parameter_1_data = parameter_1_data['value__' + type] if parameter_1_data['value__' + type] else 0
            parameter_1_report_data.append(parameter_1_data)
            if parameter_2:
                parameter_2_data = DeviceData.objects.filter(log__inserted_on__date=end_date, parameter__device_id=device_id, parameter__key=parameter_2)
                parameter_2_data = parameter_2_data.aggregate(Avg('value')) if type == 'avg' else parameter_2_data.aggregate(Sum('value'))
                parameter_2_data = parameter_2_data['value__' + type] if parameter_2_data['value__' + type] else 0
                parameter_2_report_data.append(parameter_2_data)
            end_date += timedelta(days=1)
        datasets = [
            {'label': parameter_1, 'data': parameter_1_report_data}
        ]
        if parameter_2_report_data:
            datasets.append({'label': parameter_2, 'data': parameter_2_report_data})
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {
                'labels': days,
                'datasets': datasets,
            }
        }
        return Response(data)


@api_view(['GET'])
@csrf_exempt
def monthly_report_view(request):
    if request.method == 'GET':
        device_id = request.query_params['device_id']
        parameter_1 = request.query_params['parameter_1']
        parameter_2 = request.query_params['parameter_2']
        type = request.query_params['type']
        start_date = datetime.strptime(request.query_params['year'] + '-01-01', '%Y-%m-%d').date()
        end_date = start_date
        months = []
        parameter_1_report_data = []
        parameter_2_report_data = []
        while start_date.year == end_date.year:
            months.append(str(end_date.month))
            parameter_1_data = DeviceData.objects.filter(log__inserted_on__month=end_date.month, log__inserted_on__year=end_date.year, parameter__device_id=device_id, parameter__key=parameter_1)
            parameter_1_data = parameter_1_data.aggregate(Avg('value')) if type == 'avg' else parameter_1_data.aggregate(Sum('value'))
            parameter_1_data = parameter_1_data['value__' + type] if parameter_1_data['value__' + type] else 0
            parameter_1_report_data.append(parameter_1_data)
            if parameter_2:
                parameter_2_data = DeviceData.objects.filter(log__inserted_on__month=end_date.month, log__inserted_on__year=end_date.year, parameter__device_id=device_id, parameter__key=parameter_2)
                parameter_2_data = parameter_2_data.aggregate(Avg('value')) if type == 'avg' else parameter_2_data.aggregate(Sum('value'))
                parameter_2_data = parameter_2_data['value__' + type] if parameter_2_data['value__' + type] else 0
                parameter_2_report_data.append(parameter_2_data)
            end_date += timedelta(days=31)
        datasets = [
            {'label': parameter_1, 'data': parameter_1_report_data}
        ]
        if parameter_2_report_data:
            datasets.append({'label': parameter_2, 'data': parameter_2_report_data})
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {
                'labels': months,
                'datasets': datasets,
            }
        }
        return Response(data)


@api_view(['GET'])
@csrf_exempt
def faults_view(request):
    if request.method == 'GET':
        user_id = request.query_params['user_id']
        start_date = datetime.strptime(request.query_params['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.query_params['end_date'], '%Y-%m-%d').date()
        faults = list(Faults.objects.filter(created_on__date__range=(start_date, end_date), device__created_by_id=user_id).values('device__name', 'fault_desc', 'fault_loc', 'r_status', 'created_on', 'seen_report'))
        for fault in faults:
            fault['created_on'] = fault['created_on'].strftime('%d-%m-%Y %H:%M:%S')
            fault['r_status'] = 'Yes' if fault['r_status'] else 'No'
            fault['seen_report'] = 'Seen' if fault['seen_report'] else 'Unseen'
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {
                'faults': faults
            }
        }
        return Response(data)