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
MQTT_TOPIC = 'tasmota/discovery/+/sensors'
MQTT_REGEX = 'tasmota/discovery/([^/]+)//sensors'
MQTT_CLIENT_ID = 'MQTTInfluxDBBridge'

influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8086, INFLUXDB_USER, INFLUXDB_PASSWORD, None)

class SensorData(NamedTuple):
    location: str
    total_in: float
    power_cur: float
    power_p1: float
    power_p2: float
    power_p3: float
    total_out: float

def on_connect(client, userdata, flags, rc):
    """ The callback for when the client receives a CONNACK response from the server."""
    print('Connected with result code ' + str(rc))
    client.subscribe(MQTT_TOPIC)

def _parse_mqtt_message(topic, payload):
    match = re.match(MQTT_REGEX, topic)
    if match:
        location = match.group(1)
        data = json.loads(payload)
        return SensorData( location, data["sn"]["MT174"]["Total_in"], data["sn"]["MT174"]["Power_cur"], data["sn"]["MT174"]["Power_p1"], data["sn"]["MT174"]["Power_p2"], data["sn"]["MT174"]["Power_p3"], data["sn"]["MT174"]["Total_out"])
    else:
        return None

def _send_sensor_data_to_influxdb(sensor_data: SensorData):
    json_body = [
        {
            'measurement': sensor_data.location,
            'fields': {
                'total_in': sensor_data.total_in,
                'power_cur': sensor_data.power_cur,
                'power_p1': sensor_data.power_p1,
                'power_p2': sensor_data.power_p2,
                'power_p3': sensor_data.power_p3,
                'total_out': sensor_data.total_out
            }
        }
    ]
    influxdb_client.write_points(json_body)

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
