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
MQTT_TOPIC = 'tele/+/SENSOR'
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
    except json.decoder.JSONDecodeError:
        return None
    return data["MT174"]

def _send_sensor_data_to_influxdb(sensor_data: dict):
    # only send, if new data > last data
    transmit_data={}
    now = time()
    for key in sensor_data.keys():
        if type(sensor_data[key])==str:
            continue
        if key in LAST_DATA:
            diff = sensor_data[key]-LAST_DATA[key]
            last_time = TIME_DATA[key]
            time_diff = now - last_time
            # ignore zeros
            if sensor_data[key] == 0.0:
                continue
            # diff is in KWh and time diff in seconds
            # calculate avg. Watts
            # KWh to Ws is *1000 and *3600
            factor = 1000 * 3600 / time_diff
            LAST_DATA[key]=sensor_data[key]
            TIME_DATA[key]=now
            if diff>=0:
                transmit_data[key]=sensor_data[key]
                transmit_data[key+"_wattavg"]=diff*factor
        else:
            # do not send first data point
            LAST_DATA[key]=sensor_data[key]
            TIME_DATA[key]=now
    if transmit_data.keys():
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
