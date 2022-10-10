from .models import *

def meters_data(user_id):
    meters = list(Meter.objects.filter(created_by_id=user_id).values('id', 'meter_name', 'poles_r', 'poles_y', 'poles_b', 'group', 'period_type', 'lat', 'lon', 'sunrise_offset', 'sunset_offset', 'on_time', 'off_time', 'is_on'))
    for meter in meters:
        meter['parameters'] = list(MetersThreshold.objects.filter(meter_id=meter['id']).values('id', 'meter_id', 'meter__meter_name', 'parameter_name', 'field_name', 'unit', 'min_thr', 'max_thr', 'notify'))
        for parameter in meter['parameters']:
            parameter['notify'] = 'Yes' if parameter['notify'] else 'No'
        meter['on_time'] = str(meter['on_time'])
        meter['off_time'] = str(meter['off_time'])
        meter['is_on'] = 'Yes' if meter['is_on'] else 'No'
    return meters