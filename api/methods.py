from .models import Device, DeviceParameter, ActivityLog

def devices_data(user_id):
    devices = list(Device.objects.filter(created_by_id=user_id).values('id', 'name', 'group', 'period_type', 'lat', 'lon', 'sunrise_offset', 'sunset_offset', 'on_time', 'off_time', 'is_on'))
    for device in devices:
        device['parameters'] = list(DeviceParameter.objects.filter(device_id=device['id']).values('id', 'device_id', 'device__name', 'name', 'key', 'unit', 'min_thr', 'max_thr', 'notify'))
        for parameter in device['parameters']:
            parameter['notify'] = 'Yes' if parameter['notify'] else 'No'
        device['on_time'] = str(device['on_time'])
        device['off_time'] = str(device['off_time'])
        device['is_on'] = 'Yes' if device['is_on'] else 'No'
    return devices


def log_activity(user_id, type):
    activity = ActivityLog(
        user_id = user_id,
        type = type
    )
    activity.save()
