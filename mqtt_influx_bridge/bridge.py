import re
from typing import NamedTuple

import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
import json

INFLUXDB_ADDRESS = '192.168.178.104'
INFLUXDB_USER = 'admin'
INFLUXDB_PASSWORD = '12gamma3'
INFLUXDB_DATABASE = 'tasmota_daten'

MQTT_ADDRESS = '192.168.178.104'
MQTT_USER = ''
MQTT_PASSWORD = ''
MQTT_TOPIC = 'tele/+/SENSOR'
MQTT_CLIENT_ID = 'MQTTInfluxDBBridge'
LAST_DATA={}

influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8086, INFLUXDB_USER, INFLUXDB_PASSWORD, None)

def on_connect(client, userdata, flags, rc):
    """ The callback for when the client receives a CONNACK response from the server."""
    print('Connected with result code ' + str(rc))
    client.subscribe(MQTT_TOPIC)

def _parse_mqtt_message(topic, payload):
    data = json.loads(payload)
    return data["MT174"]

def _send_sensor_data_to_influxdb(sensor_data: dict):
    # only send, if new data > last data
    transmit_data={}
    for key in sensor_data.keys():
        if type(sensor_data[key])==str:
            continue
        if key in LAST_DATA:
            diff = sensor_data[key]-LAST_DATA[key]
            LAST_DATA[key]=sensor_data[key]
#            if diff<=0.0:
#                continue
            transmit_data[key]=sensor_data[key]
        else:
            # do not send first data point
            LAST_DATA[key]=sensor_data[key]
    if transmit_data.keys():
        json_body = [
            {
                'measurement': "MT174",
                'fields': sensor_data
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
