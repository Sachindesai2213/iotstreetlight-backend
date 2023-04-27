import json
import os
from datetime import datetime, timedelta

from Adafruit_IO import Client, Data
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.db.models import Avg, Sum
from rest_framework import generics
from rest_framework.decorators import (api_view, authentication_classes,
                                       permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication

from .models import (ActivityLog, Device, DeviceConfiguration, DeviceData,
                     DeviceDataLog, DeviceParameter, Faults)
from .serializers import (ActivityLogSerializer, DeviceConfigurationSerializer,
                          DeviceParameterSerializer, DeviceSerializer,
                          FaultSerializer, UserSerializer)


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
@authentication_classes([JWTTokenUserAuthentication])
@permission_classes([IsAuthenticated])
def dashboard_data_view(request):
    if request.method == 'GET':
        user_id = request.user.id
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
        power_consumption_month = DeviceData.objects.filter(
            log__inserted_on__month=current_date.month,
            log__inserted_on__year=current_date.year,
            parameter__device__created_by_id=user_id,
            parameter__name__contains='Power'
        ).aggregate(Sum('value'))
        data = {
            'dashboard_data': [
                {
                    'title': "POWER - TODAY",
                    'value': power_consumption_today['value__sum'] or 'N/A',
                    'isIncreased': True,
                    'percentage': 0,
                    'icon': "usage",
                    'link': "/reports"
                },
                {
                    'title': "POWER - CURRENT MONTH",
                    'value': power_consumption_month['value__sum'] or 'N/A',
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
        user_id = self.request.user.id
        devices = Device.objects.filter(created_by_id=user_id)
        return devices

    def perform_create(self, serializer):
        serializer.save(created_by_id=self.request.user.id)


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


class DeviceConfigurationsView(generics.CreateAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceConfigurationSerializer
    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by_id=self.request.user.id)


@api_view(['PUT'])
@authentication_classes([JWTTokenUserAuthentication])
@permission_classes([IsAuthenticated])
def device_configurations_view(request):
    if request.method == 'PUT':
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

    def get_queryset(self):
        activities = ActivityLog.objects.filter()
        return activities


@api_view(['GET'])
@authentication_classes([JWTTokenUserAuthentication])
@permission_classes([IsAuthenticated])
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
                key = parameter['key']
                log[key] = device_data[key] if key in device_data else ''
        data = {
            'reports': device_data_logs,
            'parameters': parameters
        }
        return Response(data)


@api_view(['GET'])
@authentication_classes([JWTTokenUserAuthentication])
@permission_classes([IsAuthenticated])
def interval_report_view(request):
    if request.method == 'GET':
        device_id = request.query_params['device_id']
        parameter_1 = request.query_params['parameter_1']
        parameter_2 = request.query_params.get('parameter_2', None)
        type = request.query_params['type']
        interval = request.query_params['interval']
        start_date = None
        end_date = None
        interval_steps = None
        if interval == 'hourly':
            date = datetime.strptime(request.query_params['date'], '%Y-%m-%d')
            start_date = date
            end_date = start_date + timedelta(days=1)
            interval_steps = timedelta(hours=1)
        elif interval == 'daily':
            month = request.query_params['month']
            start_date = datetime.strptime(f'{month}-01', '%Y-%m-%d')
            end_date = start_date + relativedelta(months=1)
            interval_steps = timedelta(days=1)
        elif interval == 'monthly':
            year = request.query_params['year']
            start_date = datetime.strptime(f'{year}-01-01', '%Y-%m-%d')
            end_date = start_date + relativedelta(years=1)
            interval_steps = relativedelta(months=1)
        labels = []
        parameter_1_report_data = []
        parameter_2_report_data = []
        while start_date < end_date:
            if interval == 'hourly':
                labels.append(str(start_date.hour))
            elif interval == 'daily':
                labels.append(str(start_date.day))
            elif interval == 'monthly':
                labels.append(str(start_date.month))
            print(start_date)
            next_date = start_date + interval_steps
            parameter_1_data = DeviceData.objects.filter(
                log__inserted_on__range=(start_date, next_date),
                parameter__device_id=device_id,
                parameter__key=parameter_1
            )
            parameter_1_data = parameter_1_data.aggregate(
                Avg('value') if type == 'avg' else Sum('value'))
            parameter_1_data = parameter_1_data[f'value__{type}'] or 0
            parameter_1_report_data.append(parameter_1_data)
            if parameter_2:
                parameter_2_data = DeviceData.objects.filter(
                    log__inserted_on__range=(start_date, next_date),
                    parameter__device_id=device_id,
                    parameter__key=parameter_2
                )
                parameter_2_data = parameter_2_data.aggregate(
                    Avg('value') if type == 'avg' else Sum('value'))
                parameter_2_data = parameter_2_data[f'value__{type}'] or 0
                parameter_2_report_data.append(parameter_2_data)
            start_date += interval_steps
        datasets = [
            {'label': parameter_1, 'data': parameter_1_report_data}
        ]
        if parameter_2_report_data:
            datasets.append(
                {'label': parameter_2, 'data': parameter_2_report_data})
    data = {
        'labels': labels,
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
        user_id = self.request.user.id
        faults = Faults.objects.select_related('device').filter(
            created_on__date__range=(start_date, end_date),
            device__created_by_id=user_id
        )
        return faults
