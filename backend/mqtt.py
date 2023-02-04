import ast
import paho.mqtt.client as mqtt
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django.setup()

from api.models import DeviceParameter, DeviceDataLog, DeviceData, Faults


def on_connect(client, userdata, flags, rc):
    print('Connected' + str(rc))
    client.subscribe('sachin3913/feeds/python')


def on_message(client, userdata, msg):
    print(msg.payload.decode())
    message_object = ast.literal_eval(msg.payload.decode())
    parameters = message_object['parameters']
    device_id = message_object['device_id']
    device_log = DeviceDataLog(
        device_id=device_id
    )
    device_log.save()
    for key, value in parameters.items():
        parameter = DeviceParameter.objects.filter(device_id=device_id, key=key).last()
        if parameter:
            device_data = DeviceData(
                parameter=parameter,
                value=value,
                log=device_log
            )
            device_data.save()
            if (value < parameter.min_thr or value > parameter.max_thr):
                fault_description = 'Below Min. Threshold' if value < parameter.min_thr else 'Above Max. Threshold'
                fault = Faults(
                    device_id=device_id,
                    fault_desc=fault_description,
                    fault_loc=parameter.name,
                    created_by_id=1
                )
                fault.save()
    print('HI')


client = mqtt.Client()
client.username_pw_set(username='sachin3913',
                       password=os.environ.get('ADAFRUIT_KEY'))
client.on_connect = on_connect
client.on_message = on_message

client.connect("io.adafruit.com", 1883, 60)
