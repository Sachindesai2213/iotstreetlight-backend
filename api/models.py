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


class Meter(models.Model):
    meter_name = models.CharField(max_length=50)
    poles_r = models.IntegerField(null=True)
    poles_y = models.IntegerField(null=True)
    poles_b = models.IntegerField(null=True)
    group = models.CharField(max_length=50, null=True)
    period_type = models.CharField(max_length=10, default='Fixed')
    lat = models.FloatField(null=True)
    lon = models.FloatField(null=True)
    sunrise_offset = models.IntegerField(null=True)
    sunset_offset = models.IntegerField(null=True)
    on_time = models.TimeField(default='18:00:00')
    off_time = models.TimeField(default='06:00:00')
    is_on = models.BooleanField(default=0)
    is_change = models.BooleanField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class MeterData(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE)
    v_r = models.FloatField()
    v_y = models.FloatField()
    v_b = models.FloatField()
    c_r = models.FloatField()
    c_y = models.FloatField()
    c_b = models.FloatField()
    p_r = models.FloatField()
    p_y = models.FloatField()
    p_b = models.FloatField()
    pf = models.FloatField()
    kvar = models.FloatField()
    freq = models.FloatField()
    kwh = models.FloatField()
    kvah = models.FloatField()
    inserted_on = models.DateTimeField(auto_now_add=True)


class MetersThreshold(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE)
    parameter_name = models.CharField(max_length=20)
    field_name = models.CharField(max_length=3)
    unit = models.CharField(max_length=3)
    min_thr = models.FloatField()
    max_thr = models.FloatField()
    notify = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Faults(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE)
    fault_desc = models.CharField(max_length=100)
    fault_loc = models.CharField(max_length=50)
    r_status = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    seen_report = models.BooleanField(default=False)