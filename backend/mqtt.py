import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from api.models import MeterData
import paho.mqtt.client as mqtt
import ast

def on_connect(client,userdata, flags, rc):
    print('Connected' + str(rc))
    client.subscribe('sachin3913/feeds/python')

def on_message(client, userdata, msg):
    message_object = ast.literal_eval(msg.payload.decode())
    meter_data = MeterData(
        meter_id = message_object['meter_id'],
        v_r = message_object['v_r'],
        v_y = message_object['v_y'],
        v_b = message_object['v_b'],
        c_r = message_object['c_r'],
        c_y = message_object['c_y'],
        c_b = message_object['c_b'],
        p_r = message_object['p_r'],
        p_y = message_object['p_y'],
        p_b = message_object['p_b'],
        pf = message_object['pf'],
        kvar = message_object['kvar'],
        freq = message_object['freq'],
        kwh = message_object['kwh'],
        kvah = message_object['kvah'],
    )
    meter_data.save()
    print('HI')

client = mqtt.Client()
client.username_pw_set(username='sachin3913', password='aio_fZRv57O3pEo4syASwo1cak7b3FoB')
client.on_connect = on_connect
client.on_message = on_message

client.connect("io.adafruit.com", 1883, 60)