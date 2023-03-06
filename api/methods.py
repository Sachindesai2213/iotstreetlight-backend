from .models import Device, DeviceParameter, ActivityLog, DeviceConfiguration

def devices_data(user_id):
    devices = list(Device.objects.filter(created_by_id=user_id).values('id', 'name', 'group', 'is_on'))
    for device in devices:
        device['parameters'] = list(DeviceParameter.objects.filter(device_id=device['id']).values('id', 'device_id', 'device__name', 'name', 'key', 'unit', 'min_thr', 'max_thr', 'notify'))
        for parameter in device['parameters']:
            parameter['notify'] = 'Yes' if parameter['notify'] else 'No'
        device['configurations'] = list(DeviceConfiguration.objects.filter(device_id=device['id']).values('id', 'device_id', 'device__name', 'name', 'key', 'value'))
    return devices


def log_activity(user_id, type):
    activity = ActivityLog(
        user_id = user_id,
        type = type
    )
    activity.save()
