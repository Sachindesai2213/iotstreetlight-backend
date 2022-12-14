from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Avg, Sum
from .models import *
from .methods import log_activity, meters_data
from datetime import datetime, timedelta
import json

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
        meters = Meter.objects.filter(created_by_id=user_id).count()
        faults = Faults.objects.filter(meter__created_by_id=user_id).count()
        power_consumption_today = MeterData.objects.filter(inserted_on__date=current_date, meter__created_by_id=user_id).aggregate(Sum('kwh'))
        power_consumption_current_month = MeterData.objects.filter(inserted_on__month=current_date.month, inserted_on__year=current_date.year, meter__created_by_id=user_id).aggregate(Sum('kwh'))
        data = {
            'flash': True,
            'message': 'Successful',
            'data': [
                {
                    'title': "POWER - TODAY",
                    'value': power_consumption_today['kwh__sum'] if power_consumption_today['kwh__sum'] else 'N/A',
                    'isIncreased': True,
                    'percentage': 0,
                    'icon': "usage",
                    'link': "/reports"
                },
                {
                    'title': "POWER - CURRENT MONTH",
                    'value': power_consumption_current_month['kwh__sum'] if power_consumption_current_month['kwh__sum'] else 'N/A',
                    'isIncreased': True,
                    'percentage': 0,
                    'icon': "power",
                    'link': "/reports"
                },
                {
                    'title': 'METERS',
                    'value': meters,
                    'isIncreased': True,
                    'percentage': 0,
                    'icon': "meters",
                    'link': "/reports"
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
def reports_view(request):
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


@api_view(['GET'])
@csrf_exempt
def hourly_report_view(request):
    if request.method == 'GET':
        user_id = request.query_params['user_id']
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
            parameter_data = MeterData.objects.filter(inserted_on__range=(start_datetime, end_datetime), meter__created_by_id=user_id)
            if type == 'avg':
                parameter_data = parameter_data.aggregate(Avg(parameter_1)) if not parameter_2 else parameter_data.aggregate(Avg(parameter_1), Avg(parameter_2))
            elif type == 'sum':
                parameter_data = parameter_data.aggregate(Sum(parameter_1)) if not parameter_2 else parameter_data.aggregate(Sum(parameter_1), Sum(parameter_2))
            parameter_1_data = parameter_data[parameter_1 + '__' + type] if parameter_data[parameter_1 + '__' + type] else 0
            parameter_1_report_data.append(parameter_1_data)
            if parameter_2:
                parameter_2_data = parameter_data[parameter_2 + '__' + type] if parameter_data[parameter_2 + '__' + type] else 0
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
        user_id = request.query_params['user_id']
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
            parameter_data = MeterData.objects.filter(inserted_on__date=end_date, meter__created_by_id=user_id)
            if type == 'avg':
                parameter_data = parameter_data.aggregate(Avg(parameter_1)) if not parameter_2 else parameter_data.aggregate(Avg(parameter_1), Avg(parameter_2))
            elif type == 'sum':
                parameter_data = parameter_data.aggregate(Sum(parameter_1)) if not parameter_2 else parameter_data.aggregate(Sum(parameter_1), Sum(parameter_2))
            parameter_1_data = parameter_data[parameter_1 + '__' + type] if parameter_data[parameter_1 + '__' + type] else 0
            parameter_1_report_data.append(parameter_1_data)
            if parameter_2:
                parameter_2_data = parameter_data[parameter_2 + '__' + type] if parameter_data[parameter_2 + '__' + type] else 0
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
        user_id = request.query_params['user_id']
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
            parameter_data = MeterData.objects.filter(inserted_on__month=end_date.month, inserted_on__year=end_date.year, meter__created_by_id=user_id)
            if type == 'avg':
                parameter_data = parameter_data.aggregate(Avg(parameter_1)) if not parameter_2 else parameter_data.aggregate(Avg(parameter_1), Avg(parameter_2))
            elif type == 'sum':
                parameter_data = parameter_data.aggregate(Sum(parameter_1)) if not parameter_2 else parameter_data.aggregate(Sum(parameter_1), Sum(parameter_2))
            parameter_1_data = parameter_data[parameter_1 + '__' + type] if parameter_data[parameter_1 + '__' + type] else 0
            parameter_1_report_data.append(parameter_1_data)
            if parameter_2:
                parameter_2_data = parameter_data[parameter_2 + '__' + type] if parameter_data[parameter_2 + '__' + type] else 0
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
