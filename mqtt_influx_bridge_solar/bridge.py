import json
import os

import paho.mqtt.client as mqtt
import requests
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

def load_config():
    config_path = os.environ.get("CONFIG_PATH", "/config/config.json")
    with open(config_path, encoding="utf-8") as config_file:
        return json.load(config_file)

def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected with result code " + str(reason_code))
    if reason_code == 0:
        for topic in userdata["topics"]:
            client.subscribe(topic)

def _parse_mqtt_message(topic, payload):
    if not (topic.endswith("/state") or topic.endswith("/properties/report")):
        return None
    try:
        message = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if not isinstance(message, dict):
        return None
    if topic.endswith("/properties/report"):
        properties = message.get("properties")
        if not isinstance(properties, dict):
            return None
        sensor_data = properties.copy()
        if "packData" in message:
            sensor_data["packData"] = message["packData"]
        return sensor_data
    return message


def _influx_fields(sensor_data):
    fields = {}
    for name, value in sensor_data.items():
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            fields[name] = json.dumps(value, separators=(",", ":"))
        else:
            fields[name] = value
    return fields


def _battery_points(sensor_data, measurement, device):
    points = []
    pack_data = sensor_data.get("packData")
    if not isinstance(pack_data, list):
        return points
    for pack in pack_data:
        if not isinstance(pack, dict) or not pack.get("sn"):
            continue
        fields = {
            name: value for name, value in pack.items()
            if name != "sn" and value is not None
            and isinstance(value, (bool, int, float, str))
        }
        if fields:
            points.append({
                "measurement": measurement + "_battery",
                "tags": {"device": device, "sn": str(pack["sn"])},
                "fields": fields,
            })
    return points


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
    except UnicodeDecodeError:
        return
    sensor_data = _parse_mqtt_message(msg.topic, payload)
    if isinstance(sensor_data, dict):
        fields = _influx_fields(sensor_data)
        topic_parts = msg.topic.strip("/").split("/")
        device = topic_parts[1] if len(topic_parts) > 1 else "unknown"
        points = _battery_points(sensor_data, userdata["measurement"], device)
        if fields:
            points.insert(0, {
                "measurement": userdata["measurement"],
                "tags": {"device": device},
                "fields": fields,
            })
        if points:
            userdata["write_api"].write(
                bucket=userdata["bucket"],
                org=userdata["org"],
                record=points,
            )

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
        url=influx["url"], token=influx["token"], org=influx["org"]
    )
    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

    connection = get_solarflow_data(
        solarflow["account"], solarflow["serial"], solarflow["api_url"]
    )

    mqtt_client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=mqtt_config["client_id"],
        userdata={
            "topics": [
                connection["appKey"] + "/#",
                "/" + connection["appKey"] + "/#",
            ],
            "measurement": influx["measurement"],
            "bucket": influx["bucket"],
            "org": influx["org"],
            "influxdb_client": influxdb_client,
            "write_api": write_api,
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
