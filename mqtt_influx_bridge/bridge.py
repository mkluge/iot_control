import re
from typing import NamedTuple

import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
from time import time
import json

INFLUXDB_ADDRESS = '192.168.178.104'
INFLUXDB_USER = 'admin'
INFLUXDB_PASSWORD = '12gamma3'
INFLUXDB_DATABASE = 'strom'

MQTT_ADDRESS = '192.168.178.104'
MQTT_USER = ''
MQTT_PASSWORD = ''
MQTT_TOPIC = 'tele/tasmota_09BDF1/SENSOR'
#MQTT_TOPIC = '#'
MQTT_CLIENT_ID = 'MQTTInfluxDBBridge'
LAST_DATA={}
TIME_DATA={}

influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8086, INFLUXDB_USER, INFLUXDB_PASSWORD, None)

def on_connect(client, userdata, flags, rc):
    """ The callback for when the client receives a CONNACK response from the server."""
    print('Connected with result code ' + str(rc))
    client.subscribe(MQTT_TOPIC)

def _parse_mqtt_message(topic, payload):
    try:
        data = json.loads(payload)
        if isinstance(data,dict) and "GS303" in data:
            return data["GS303"]
        return None
    except json.decoder.JSONDecodeError:
        return None

def _send_sensor_data_to_influxdb(sensor_data: dict):
#tele/tasmota_09BDF1/SENSOR = {"Time":"2023-06-18T15:22:20","GS303":{"Total_in":31.834,"Power_cur":-93,"Total_out":5.021,"Meter_id":"5a5041"}}'
    # only send, if new data > last data
    diffKeys = ["Total_in","Total_out"]
    transmit_data={}
    transmit_data["total_1"]=sensor_data["Total_in"]
    transmit_data["total_out"]=sensor_data["Total_out"]
    transmit_data["power_cur"]=float(sensor_data["Power_cur"])
    json_body = [
        {
            'measurement': "MT174",
            'fields': transmit_data
        }
    ]
    print(json.dumps(json_body))
    print(influxdb_client.write_points(json_body))

def on_message(client, userdata, msg):
    """The callback for when a PUBLISH message is received from the server."""
    print(msg.topic + ' ' + str(msg.payload))
    sensor_data = _parse_mqtt_message(msg.topic, msg.payload.decode('utf-8'))
    if sensor_data is not None:
        _send_sensor_data_to_influxdb(sensor_data)

def _init_influxdb_database():
    databases = influxdb_client.get_list_database()
    if len(list(filter(lambda x: x['name'] == INFLUXDB_DATABASE, databases))) == 0:
        influxdb_client.create_database(INFLUXDB_DATABASE)
    influxdb_client.switch_database(INFLUXDB_DATABASE)

def main():
    _init_influxdb_database()

    mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(MQTT_ADDRESS, 1883)
    mqtt_client.loop_forever()


if __name__ == '__main__':
    print('MQTT to InfluxDB bridge')
    main()
