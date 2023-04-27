from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (ActivityLog, Device, DeviceConfiguration, DeviceParameter,
                     Faults, UserInfo)


class UserInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserInfo
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    user_info = UserInfoSerializer()

    class Meta:
        model = User
        fields = '__all__'


class ActivityLogSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = ActivityLog
        fields = '__all__'


class DeviceParameterSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.name')

    class Meta:
        model = DeviceParameter
        fields = '__all__'


class DeviceConfigurationSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.name', read_only=True)

    class Meta:
        model = DeviceConfiguration
        exclude = ['created_by']


class FaultSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.name')

    class Meta:
        model = Faults
        fields = '__all__'


class DeviceSerializer(serializers.ModelSerializer):
    faults = FaultSerializer(many=True, read_only=True)
    device_parameters = DeviceParameterSerializer(many=True, read_only=True)
    device_configurations = DeviceConfigurationSerializer(many=True,
                                                          read_only=True)

    class Meta:
        model = Device
        exclude = ['created_by']
