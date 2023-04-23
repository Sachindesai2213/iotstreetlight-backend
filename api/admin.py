from django.contrib import admin

from .models import (ActivityLog, Device, DeviceConfiguration, DeviceData,
                     DeviceDataLog, DeviceParameter, Faults, UserInfo)

# Register your models here.
admin.site.register(UserInfo)
admin.site.register(Device)
admin.site.register(DeviceDataLog)
admin.site.register(DeviceData)
admin.site.register(DeviceParameter)
admin.site.register(Faults)
admin.site.register(ActivityLog)
admin.site.register(DeviceConfiguration)
