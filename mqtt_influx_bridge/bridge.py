import json
import os

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS


def load_config():
    config_path = os.environ.get("CONFIG_PATH", "/config/config.json")
    with open(config_path, encoding="utf-8") as config_file:
        return json.load(config_file)


def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected with result code " + str(reason_code))
    if reason_code == 0:
        client.subscribe(userdata["topic"])


def _parse_mqtt_message(payload):
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict) and isinstance(data.get("GS303"), dict):
        return data["GS303"]
    return None


def _influx_fields(sensor_data):
    return {
        "total_1": sensor_data["Total_in"],
        "total_out": sensor_data["Total_out"],
        "power_cur": float(sensor_data["Power_cur"]),
    }


def on_message(client, userdata, msg):
    sensor_data = _parse_mqtt_message(msg.payload.decode("utf-8"))
    if sensor_data is not None:
        userdata["write_api"].write(
            bucket=userdata["bucket"],
            org=userdata["org"],
            record={
                "measurement": userdata["measurement"],
                "fields": _influx_fields(sensor_data),
            },
        )


def main():
    config = load_config()
    influx = config["influxdb"]
    mqtt_config = config["mqtt"]

    influxdb_client = InfluxDBClient(
        url=influx["url"], token=influx["token"], org=influx["org"]
    )
    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

    mqtt_client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=mqtt_config["client_id"],
        userdata={
            "topic": mqtt_config["topic"],
            "measurement": influx["measurement"],
            "bucket": influx["bucket"],
            "org": influx["org"],
            "influxdb_client": influxdb_client,
            "write_api": write_api,
        },
    )
    if mqtt_config["user"]:
        mqtt_client.username_pw_set(mqtt_config["user"], mqtt_config["password"])
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(mqtt_config["host"], mqtt_config["port"])
    mqtt_client.loop_forever()


if __name__ == "__main__":
    print("MQTT to InfluxDB bridge")
    main()
