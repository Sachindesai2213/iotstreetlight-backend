from django.contrib import admin
from .models import UserInfo, Meter, MeterData, MetersThreshold, Faults, ActivityLog

# Register your models here.
admin.site.register(UserInfo)
admin.site.register(Meter)
admin.site.register(MeterData)
admin.site.register(MetersThreshold)
admin.site.register(Faults)
admin.site.register(ActivityLog)
