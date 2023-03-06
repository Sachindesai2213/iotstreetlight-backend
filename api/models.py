from django.db import models
from django.conf import settings

# Create your models here.
class UserInfo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contact = models.CharField(max_length=10)


class ActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=25)
    timestamp = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)


class Device(models.Model):
    name = models.CharField(max_length=50)
    group = models.CharField(max_length=50, null=True)
    is_on = models.BooleanField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class DeviceConfiguration(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=20)
    value = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class DeviceParameter(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=20)
    unit = models.CharField(max_length=3)
    min_thr = models.FloatField(null=True)
    max_thr = models.FloatField(null=True)
    notify = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    

class DeviceDataLog(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    inserted_on = models.DateTimeField(auto_now_add=True)


class DeviceData(models.Model):
    parameter = models.ForeignKey(DeviceParameter, on_delete=models.CASCADE)
    value = models.FloatField(default=0)
    log = models.ForeignKey(DeviceDataLog, on_delete=models.CASCADE, null=True)


class Faults(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    fault_desc = models.CharField(max_length=100)
    fault_loc = models.CharField(max_length=50)
    r_status = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    seen_report = models.BooleanField(default=False)