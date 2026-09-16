#!/usr/bin/env python3
"""Connect to the SolarFlow MQTT broker and pretty-print every visible message."""

import argparse
import base64
import json
import os
import signal
import sys
import threading
import uuid
from datetime import datetime
from urllib.parse import urlparse

import paho.mqtt.client as mqtt
import requests


def load_config(path):
    with open(path, encoding="utf-8") as config_file:
        return json.load(config_file)


def get_solarflow_connection(solarflow):
    response = requests.post(
        solarflow["api_url"],
        json={
            "snNumber": solarflow["serial"],
            "account": solarflow["account"],
        },
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    connection = body.get("data")
    if not isinstance(connection, dict):
        raise RuntimeError("SolarFlow API response contains no connection data")

    missing = {"appKey", "secret", "mqttUrl", "port"} - connection.keys()
    if missing:
        raise RuntimeError(
            "SolarFlow API response is missing: " + ", ".join(sorted(missing))
        )
    return connection


def parse_broker_url(value, api_port):
    # SolarFlow normally returns a bare hostname, but accepting URI forms makes
    # this useful if the API changes to mqtt[s]:// or ws[s]:// URLs.
    parsed = urlparse(value if "://" in value else "//" + value)
    scheme = parsed.scheme.lower()
    host = parsed.hostname or parsed.path
    port = parsed.port or int(api_port)
    transport = "websockets" if scheme in {"ws", "wss"} else "tcp"
    use_tls = scheme in {"mqtts", "ssl", "tls", "wss"}
    if not host:
        raise RuntimeError("SolarFlow API returned an invalid MQTT URL")
    return host, port, transport, use_tls


def printable_payload(payload):
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return {
            "encoding": "base64",
            "bytes": len(payload),
            "data": base64.b64encode(payload).decode("ascii"),
        }

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def reason_failed(reason):
    try:
        return reason.is_failure
    except AttributeError:
        return int(reason) >= 128


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_failed(reason_code):
        print(f"Connection rejected: {reason_code}", file=sys.stderr, flush=True)
        userdata["failed"].set()
        client.disconnect()
        return

    print(
        f"Connected to {userdata['host']}:{userdata['port']}; subscribing to #",
        flush=True,
    )
    result, message_id = client.subscribe("#", qos=0)
    if result != mqtt.MQTT_ERR_SUCCESS:
        print(f"Could not send subscription: {mqtt.error_string(result)}", file=sys.stderr)
        userdata["failed"].set()
        client.disconnect()
        return
    userdata["subscriptions"][message_id] = "#"


def on_subscribe(client, userdata, message_id, reason_codes, properties):
    topic = userdata["subscriptions"].pop(message_id, "unknown")
    rejected = not reason_codes or any(reason_failed(code) for code in reason_codes)
    if not rejected:
        print(f"Subscription active: {topic}\n", flush=True)
        return

    if topic == "#":
        # Some broker ACLs reject a global wildcard while allowing the account
        # namespace. Try both topic shapes used by SolarFlow firmware.
        print("Broker rejected #; trying the SolarFlow account namespace", flush=True)
        submitted = 0
        for fallback in (
            f"{userdata['app_key']}/#",
            f"/{userdata['app_key']}/#",
        ):
            result, fallback_id = client.subscribe(fallback, qos=0)
            if result == mqtt.MQTT_ERR_SUCCESS:
                userdata["subscriptions"][fallback_id] = fallback
                submitted += 1
        if not submitted:
            print("Could not send a fallback subscription", file=sys.stderr, flush=True)
            userdata["failed"].set()
            client.disconnect()
        return

    print(f"Subscription rejected: {topic}", file=sys.stderr, flush=True)
    if not userdata["subscriptions"]:
        userdata["failed"].set()
        client.disconnect()


def on_message(client, userdata, message):
    timestamp = datetime.now().astimezone().isoformat(timespec="milliseconds")
    metadata = f"{timestamp}  topic={message.topic!r}  qos={message.qos}  retained={message.retain}"
    print(metadata)
    print(json.dumps(printable_payload(message.payload), indent=2, ensure_ascii=False))
    print(flush=True)


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    if reason_failed(reason_code) and not userdata["stopping"].is_set():
        print(f"Unexpected MQTT disconnect: {reason_code}", file=sys.stderr, flush=True)
        userdata["failed"].set()


def parse_args():
    default_config = os.environ.get(
        "CONFIG_PATH", os.path.join(os.path.dirname(__file__), "config.json")
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", default=default_config, help="configuration JSON (default: %(default)s)"
    )
    parser.add_argument(
        "--seconds",
        type=float,
        help="disconnect after this many seconds (default: run until Ctrl-C)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.seconds is not None and args.seconds <= 0:
        raise ValueError("--seconds must be greater than zero")

    config = load_config(args.config)
    print("Requesting MQTT credentials for the configured SolarFlow device...", flush=True)
    connection = get_solarflow_connection(config["solarflow"])
    host, port, transport, use_tls = parse_broker_url(
        str(connection["mqttUrl"]), connection["port"]
    )

    userdata = {
        "app_key": connection["appKey"],
        "failed": threading.Event(),
        "host": host,
        "port": port,
        "stopping": threading.Event(),
        "subscriptions": {},
    }
    configured_id = config.get("mqtt", {}).get("client_id", "SolarFlowMQTTTest")
    client_id = f"{configured_id}-test-{uuid.uuid4().hex[:8]}"
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
        userdata=userdata,
        transport=transport,
    )
    client.username_pw_set(connection["appKey"], connection["secret"])
    if use_tls:
        client.tls_set()
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    timer = None

    def stop(*_args):
        if userdata["stopping"].is_set():
            return
        userdata["stopping"].set()
        print("\nDisconnecting...", flush=True)
        client.disconnect()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    if args.seconds is not None:
        timer = threading.Timer(args.seconds, stop)
        timer.daemon = True
        timer.start()

    print(f"Client ID: {client_id}")
    client.connect(host, port, keepalive=60)
    try:
        client.loop_forever()
    finally:
        if timer is not None:
            timer.cancel()

    return 1 if userdata["failed"].is_set() else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, ValueError, RuntimeError, requests.RequestException) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
