import re
from typing import NamedTuple

import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
from time import time
import json
import requests

INFLUXDB_ADDRESS = '192.168.178.104'
INFLUXDB_USER = 'admin'
INFLUXDB_PASSWORD = '12gamma3'
INFLUXDB_DATABASE = 'strom'

SOLAR_FLOW_SN='PO1HLEJLFC03388'
SOLAR_FLOW_ACCOUNT='vollseil@mailbox.org'
ZENDURE_URL='https://app.zendure.tech/v2/developer/api/apply'


MQTT_ADDRESS = ''
MQTT_PORT = ''
MQTT_USER = ''
MQTT_PASSWORD = ''
MQTT_TOPIC = ''
MQTT_CLIENT_ID = 'MQTTInfluxDBBridgeSolar'

influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8086, INFLUXDB_USER, INFLUXDB_PASSWORD, None)

def on_connect(client, userdata, flags, rc):
    global MQTT_TOPIC
    """ The callback for when the client receives a CONNACK response from the server."""
    print('Connected with result code ' + str(rc))
    print(MQTT_TOPIC)
    client.subscribe(MQTT_TOPIC)

def _parse_mqtt_message(topic: str, payload):
    if topic.endswith("/state"):
        print(payload)
        try:
            data = json.loads(payload)
            return data
        except json.decoder.JSONDecodeError:
            return None

def _send_sensor_data_to_influxdb(sensor_data: dict):
    json_body = [
        {
            'measurement': "solarflow",
            'fields': sensor_data
        }
    ]
#    print(json.dumps(json_body))
    print(influxdb_client.write_points(json_body))

def on_message(client, userdata, msg):
    """The callback for when a PUBLISH message is received from the server."""
    #print(msg.topic + ' ' + str(msg.payload))
    #print(userdata)
    sensor_data = _parse_mqtt_message(msg.topic, msg.payload.decode('utf-8'))
    if sensor_data is not None:
        _send_sensor_data_to_influxdb(sensor_data)

def _init_influxdb_database():
    databases = influxdb_client.get_list_database()
    if len(list(filter(lambda x: x['name'] == INFLUXDB_DATABASE, databases))) == 0:
        influxdb_client.create_database(INFLUXDB_DATABASE)
    influxdb_client.switch_database(INFLUXDB_DATABASE)

def get_solarflow_data( account, serial):
    r = requests.post( ZENDURE_URL, json={  
        "snNumber": serial,
        "account": account
    })
    if r.status_code!=200:
        print("error getting data")
    else:
        return r.json()

def main():
    global MQTT_TOPIC
    _init_influxdb_database()
    solar_flow_data = get_solarflow_data( SOLAR_FLOW_ACCOUNT, SOLAR_FLOW_SN)
    print(solar_flow_data)
    MQTT_USER = solar_flow_data["data"]["appKey"]
    MQTT_PASSWORD = solar_flow_data["data"]["secret"]
    MQTT_ADDRESS = solar_flow_data["data"]["mqttUrl"]
    MQTT_PORT = solar_flow_data["data"]["port"]
    MQTT_TOPIC = MQTT_USER + "/#"

    mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(MQTT_ADDRESS, MQTT_PORT)
    mqtt_client.loop_forever()

if __name__ == '__main__':
    print('MQTT to InfluxDB bridge Solar')
    main()
