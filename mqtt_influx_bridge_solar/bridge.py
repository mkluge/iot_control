import json
import os

import paho.mqtt.client as mqtt
import requests
from influxdb import InfluxDBClient

def load_config():
    config_path = os.environ.get("CONFIG_PATH", "/config/config.json")
    with open(config_path, encoding="utf-8") as config_file:
        return json.load(config_file)

def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected with result code " + str(reason_code))
    if reason_code == 0:
        client.subscribe(userdata["topic"])

def _parse_mqtt_message(topic, payload):
    if topic.endswith("/state"):
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return None
    return None

def on_message(client, userdata, msg):
    sensor_data = _parse_mqtt_message(msg.topic, msg.payload.decode("utf-8"))
    if sensor_data is not None:
        userdata["influxdb_client"].write_points([
            {"measurement": userdata["measurement"], "fields": sensor_data}
        ])

def _init_influxdb_database(client, database):
    databases = client.get_list_database()
    if not any(item["name"] == database for item in databases):
        client.create_database(database)
    client.switch_database(database)

def get_solarflow_data(account, serial, url):
    response = requests.post(url, json={"snNumber": serial, "account": account}, timeout=30)
    response.raise_for_status()
    return response.json()["data"]

def main():
    config = load_config()
    influx = config["influxdb"]
    solarflow = config["solarflow"]
    mqtt_config = config["mqtt"]

    influxdb_client = InfluxDBClient(
        influx["host"], influx["port"], influx["user"], influx["password"], None
    )
    _init_influxdb_database(influxdb_client, influx["database"])

    connection = get_solarflow_data(
        solarflow["account"], solarflow["serial"], solarflow["api_url"]
    )

    mqtt_client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=mqtt_config["client_id"],
        userdata={
            "topic": connection["appKey"] + "/#",
            "measurement": influx["measurement"],
            "influxdb_client": influxdb_client,
        },
    )
    mqtt_client.username_pw_set(connection["appKey"], connection["secret"])
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(connection["mqttUrl"], int(connection["port"]))
    mqtt_client.loop_forever()

if __name__ == '__main__':
    print("MQTT to InfluxDB bridge Solar")
    main()
