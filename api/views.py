import json
import os
from datetime import datetime, timedelta

from Adafruit_IO import Client, Data
from django.contrib.auth.models import User
from django.db.models import Avg, Sum
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication

from .methods import log_activity
from .models import (ActivityLog, Device, DeviceConfiguration, DeviceData,
                     DeviceDataLog, DeviceParameter, Faults)
from .serializers import (ActivityLogSerializer, DeviceParameterSerializer,
                          DeviceSerializer, FaultSerializer, UserSerializer)


# Create your views here.
class UsersView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]


class UserView(generics.RetrieveAPIView, generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]


@api_view(['GET'])
def dashboard_data_view(request):
    if request.method == 'GET':
        user_id = request.query_params['user_id']
        current_date = datetime.now().date()
        devices = Device.objects.filter(created_by_id=user_id).values('id')
        for device in devices:
            latitude_configuration = DeviceConfiguration.objects.filter(
                device_id=device['id'], name='Latitude').last()
            longitude_configuration = DeviceConfiguration.objects.filter(
                device_id=device['id'], name='Longitude').last()
            if latitude_configuration and longitude_configuration:
                device['latitude'] = latitude_configuration.value
                device['longitude'] = longitude_configuration.value
        device_count = len(devices)
        faults = Faults.objects.filter(device__created_by_id=user_id).count()
        power_consumption_today = DeviceData.objects.filter(
            log__inserted_on__date=current_date,
            parameter__device__created_by_id=user_id,
            parameter__name__contains='Power'
        ).aggregate(Sum('value'))
        power_consumption_current_month = DeviceData.objects.filter(
            log__inserted_on__month=current_date.month, log__inserted_on__year=current_date.year, parameter__device__created_by_id=user_id,
            parameter__name__contains='Power'
        ).aggregate(Sum('value'))
        data = {
            'dashboard_data': [
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
                    'value': device_count,
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
            ],
            'devices': devices
        }
        return Response(data)


class DevicesView(generics.ListAPIView, generics.CreateAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        devices = Device.objects.filter(created_by_id=user_id)
        return devices

    def perform_create(self, serializer):
        serializer.save(created_by_id=self.request.data.get('user_id'))


class DeviceView(generics.UpdateAPIView, generics.DestroyAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    lookup_field = 'id'
    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        return instance


class DeviceParametersView(generics.CreateAPIView):
    queryset = DeviceParameter.objects.all()
    serializer_class = DeviceParameterSerializer
    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]


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
            device_id=device_id,
            name=name,
            key=key,
            value=value,
            created_by_id=user_id
        )
        device_configuration.save()
        log_activity(user_id, 'Added Device Configuration ID#' +
                     str(device_configuration.id))
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {}
        }
        return Response(data)
    elif request.method == 'PUT':
        configurations = list(DeviceConfiguration.objects.filter(
            device_id=request.data['id']).values(
            'id', 'device_id', 'device__name', 'name', 'key', 'value'))
        data = json.dumps(configurations)
        aio = Client('sachin3913', os.environ.get('ADAFRUIT_KEY'))
        data = Data(value=data)
        aio.create_data('python', data)
        data = {
            'flash': True,
            'message': 'Successful',
            'data': {}
        }
        return Response(data)


class ActivitiesView(generics.ListAPIView):
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer


@api_view(['GET'])
@csrf_exempt
def reports_view(request):
    if request.method == 'GET':
        device_id = request.query_params['device_id']
        start_date = datetime.strptime(
            request.query_params['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(
            request.query_params['end_date'], '%Y-%m-%d').date()
        parameters = list(DeviceParameter.objects.filter(
            device_id=device_id).values('key', 'name'))
        device_data_logs = list(DeviceDataLog.objects.filter(
            inserted_on__date__range=(start_date, end_date),
            device_id=device_id
        ).values('id', 'device_id', 'device__name', 'inserted_on'))
        for log in device_data_logs:
            log['inserted_on'] = log['inserted_on'].strftime(
                '%d-%m-%Y %H:%M:%S')
            device_data = dict(DeviceData.objects.filter(
                log_id=log['id']).values_list('parameter__key', 'value'))
            for parameter in parameters:
                log[parameter['key']] = device_data[parameter['key']
                                                    ] if parameter['key'] in device_data else ''
        data = {
            'reports': device_data_logs,
            'parameters': parameters
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
            parameter_1_data = DeviceData.objects.filter(
                log__inserted_on__range=(start_datetime, end_datetime),
                parameter__device_id=device_id,
                parameter__key=parameter_1
            )
            parameter_1_data = parameter_1_data.aggregate(
                Avg('value')) if type == 'avg' else parameter_1_data.aggregate(Sum('value'))
            parameter_1_data = parameter_1_data['value__' +
                                                type] if parameter_1_data['value__' + type] else 0
            parameter_1_report_data.append(parameter_1_data)
            if parameter_2:
                parameter_2_data = DeviceData.objects.filter(
                    log__inserted_on__range=(start_datetime, end_datetime),
                    parameter__device_id=device_id,
                    parameter__key=parameter_2
                )
                parameter_2_data = parameter_2_data.aggregate(
                    Avg('value')) if type == 'avg' else parameter_2_data.aggregate(Sum('value'))
                parameter_2_data = parameter_2_data['value__' +
                                                    type] if parameter_2_data['value__' + type] else 0
                parameter_2_report_data.append(parameter_2_data)
            start_datetime += timedelta(hours=1)
            end_datetime += timedelta(hours=1)
        datasets = [
            {'label': parameter_1, 'data': parameter_1_report_data}
        ]
        if parameter_2_report_data:
            datasets.append(
                {'label': parameter_2, 'data': parameter_2_report_data})
        data ={
            'labels': hours,
            'datasets': datasets,
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
        start_date = datetime.strptime(
            request.query_params['month'] + '-01', '%Y-%m-%d').date()
        end_date = start_date
        days = []
        parameter_1_report_data = []
        parameter_2_report_data = []
        while start_date.month == end_date.month:
            days.append(str(end_date.day))
            parameter_1_data = DeviceData.objects.filter(
                log__inserted_on__date=end_date,
                parameter__device_id=device_id,
                parameter__key=parameter_1
            )
            parameter_1_data = parameter_1_data.aggregate(
                Avg('value')) if type == 'avg' else parameter_1_data.aggregate(Sum('value'))
            parameter_1_data = parameter_1_data['value__' +
                                                type] if parameter_1_data['value__' + type] else 0
            parameter_1_report_data.append(parameter_1_data)
            if parameter_2:
                parameter_2_data = DeviceData.objects.filter(
                    log__inserted_on__date=end_date,
                    parameter__device_id=device_id,
                    parameter__key=parameter_2
                )
                parameter_2_data = parameter_2_data.aggregate(
                    Avg('value')) if type == 'avg' else parameter_2_data.aggregate(Sum('value'))
                parameter_2_data = parameter_2_data['value__' +
                                                    type] if parameter_2_data['value__' + type] else 0
                parameter_2_report_data.append(parameter_2_data)
            end_date += timedelta(days=1)
        datasets = [
            {'label': parameter_1, 'data': parameter_1_report_data}
        ]
        if parameter_2_report_data:
            datasets.append(
                {'label': parameter_2, 'data': parameter_2_report_data})
        data = {
            'labels': days,
            'datasets': datasets,
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
        start_date = datetime.strptime(
            request.query_params['year'] + '-01-01', '%Y-%m-%d').date()
        end_date = start_date
        months = []
        parameter_1_report_data = []
        parameter_2_report_data = []
        while start_date.year == end_date.year:
            months.append(str(end_date.month))
            parameter_1_data = DeviceData.objects.filter(
                log__inserted_on__month=end_date.month,
                log__inserted_on__year=end_date.year,
                parameter__device_id=device_id,
                parameter__key=parameter_1
            )
            parameter_1_data = parameter_1_data.aggregate(
                Avg('value')) if type == 'avg' else parameter_1_data.aggregate(Sum('value'))
            parameter_1_data = parameter_1_data['value__' +
                                                type] if parameter_1_data['value__' + type] else 0
            parameter_1_report_data.append(parameter_1_data)
            if parameter_2:
                parameter_2_data = DeviceData.objects.filter(
                    log__inserted_on__month=end_date.month,
                    log__inserted_on__year=end_date.year,
                    parameter__device_id=device_id,
                    parameter__key=parameter_2
                )
                parameter_2_data = parameter_2_data.aggregate(
                    Avg('value')) if type == 'avg' else parameter_2_data.aggregate(Sum('value'))
                parameter_2_data = parameter_2_data['value__' +
                                                    type] if parameter_2_data['value__' + type] else 0
                parameter_2_report_data.append(parameter_2_data)
            end_date += timedelta(days=31)
        datasets = [
            {'label': parameter_1, 'data': parameter_1_report_data}
        ]
        if parameter_2_report_data:
            datasets.append(
                {'label': parameter_2, 'data': parameter_2_report_data})
        data = {
            'labels': months,
            'datasets': datasets,
        }
        return Response(data)


class FaultsView(generics.ListAPIView):
    queryset = Faults.objects.all()
    serializer_class = FaultSerializer
    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        user_id = self.request.query_params.get('user_id')
        faults = Faults.objects.select_related('device').filter(
            created_on__date__range=(start_date, end_date),
            device__created_by_id=user_id
        )
        return faults
