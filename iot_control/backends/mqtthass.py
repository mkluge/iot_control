#!/usr/bin/python3

import json
from typing import Dict, List
from iot_control.iotbackendbase import IoTBackendBase
from iot_control.iotdevicebase import IoTDeviceBase
from iot_control.iotfactory import IoTFactory

import paho.mqtt.client as mqtt


@IoTFactory.register_backend("mqtt_hass")
class BackendMqttHass(IoTBackendBase):

    avail_topics = []
    state_topics = {}
    command_topics = {}
    devices = []

    def __init__(self, **kwargs):
        super().__init__()
        config = kwargs.get("config", None)
        self.config = config
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.mqtt_callback_connect
        self.mqtt_client.on_message = self.mqtt_callback_message
        self.mqtt_client.on_disconnect = self.mqtt_callback_disconnect
        self.mqtt_client.connect(
            self.config['server'], self.config['port'], 60)
        self.mqtt_client.loop_start()

#        if config['user'] and config['password']:
#            self.mqtt_client.username_pw_set(
#                username=config['user'], password=config['password'])

    def register_device(self, device: IoTDeviceBase) -> None:
        self.devices.append(device)

    def shutdown(self):
        for avail_topic in self.avail_topics:
            self.mqtt_client.publish(avail_topic, self.config.offline_payload)
        self.mqtt_client.disconnect()
        self.mqtt_client.loop_stop()

    def workon(self, thing: IoTDeviceBase, data: Dict):
        for entry in data:
            if entry in self.state_topics:
                val = {entry: data[entry]}
                state_topic = self.state_topics[entry]
                self.mqtt_client.publish(state_topic, json.dumps(val))

    def announce(self):
        for device in self.devices:
            # is it a sensor or a switch
            if "sensors" in device.conf:
                # get list of sensors on device
                sensors = device.conf["sensors"]
                # create a state topic for everyone
                try:
                    sensor_cfg = device.conf["sensors"]
                    for sensor in sensors:
                        try:
                            sconf = sensor_cfg[sensor]
                            config_topic = "{}/sensor/{}/{}/config".format(
                                self.config["hass_discovery_prefix"],
                                sconf["unique_id"], sensor)
                            state_topic = "{}/sensor/{}/state".format(
                                self.config["hass_discovery_prefix"],
                                sconf["unique_id"])
                            avail_topic = "{}/sensor/{}/avail".format(
                                self.config["hass_discovery_prefix"],
                                sconf["unique_id"])
                            self.avail_topics.append(avail_topic)
                            self.state_topics[sensor] = state_topic
                            conf_dict = {
                                "device_class": sconf["device_class"],
                                "name": sconf["name"],
                                "unique_id": sconf["unique_id"],
                                "state_topic": state_topic,
                                "availability_topic": avail_topic,
                                "unit_of_measurement": sconf["unit_of_measurement"],
                                "value_template": "{{ value_json." + sensor + " }}",
                                "expire_after": sconf["expire_after"],
                                "payload_available": self.config["online_payload"],
                                "payload_not_available": self.config["offline_payload"]
                            }
                            payload = json.dumps(conf_dict)

                            print("publishing: {}".format(payload))
                            result = self.mqtt_client.publish(
                                config_topic, payload)
                            print("wait for publish")
                            result.wait_for_publish()
                            print("publish ")
                            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                                print("unable to publish")
                            print(result)

                            self.mqtt_client.publish(
                                avail_topic, self.config["online_payload"])
                        except Exception as e:
                            print("config for sensor {} wrong: {}".format(sensor, e))
                except:
                    print("error announcing sensor")
            else:
                # it is a switch
                # get list of switches on device
                switches = device.sensor_list()
                # create a state topic for everyone
                try:
                    switches_cfg = device.conf["names"]
                    for switch in switches:
                        try:
                            sconf = switches_cfg[switch]
                            print(sconf)
                            config_topic = "{}/switch/{}/{}/config".format(
                                self.config["hass_discovery_prefix"],
                                sconf["unique_id"], switch)
                            state_topic = "{}/switch/{}/state".format(
                                self.config["hass_discovery_prefix"],
                                sconf["unique_id"])
                            avail_topic = "{}/switch/{}/avail".format(
                                self.config["hass_discovery_prefix"],
                                sconf["unique_id"])
                            command_topic = "{}/switch/{}/command".format(
                                self.config["hass_discovery_prefix"],
                                sconf["unique_id"])
                            self.avail_topics.append(avail_topic)
                            self.state_topics[switch] = state_topic
                            conf_dict = {
                                "name": sconf["name"],
                                "unique_id": sconf["unique_id"],
                                "state_topic": state_topic,
                                "availability_topic": avail_topic,
                                "command_topic": command_topic,
                                "value_template": "{{ value_json." + switch + " }}",
                                "payload_available": self.config["online_payload"],
                                "payload_not_available": self.config["offline_payload"],
                                "payload_on": self.config["payload_on"],
                                "payload_off": self.config["payload_off"],
                                "state_on": self.config["payload_on"],
                                "state_off": self.config["payload_off"],
                                "optimistic": "false"
                                # qos: 0
                                # retain: true
                            }
                            payload = json.dumps(conf_dict)

                            print("publishing: {}".format(payload))
                            result = self.mqtt_client.publish(
                                config_topic, payload)
                            print("wait for publish")
                            result.wait_for_publish()
                            print("published")
                            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                                print("publish result not OK")
                            print(result)

                            self.mqtt_client.publish(
                                avail_topic, self.config["online_payload"])

                            # now subscribe to the command topic
                            (result, mid) = self.mqtt_client.subscribe(
                                command_topic)
                            print("subscription result: "+str(result))
                            self.command_topics[command_topic] = [
                                device, switch, state_topic
                            ]

                        except:
                            print("error announcing switch {}".format(switch))
                except:
                    print("error missing config for switches")

    # The callback for when the client receives a CONNACK response from the server.

    def mqtt_callback_connect(self, client, userdata, flags, rc):

        (result, mid) = self.mqtt_client.subscribe("homeassistant/status")
        print("Got subscription result for " +
              "homeassistant/status"+":"+str(result))
#        self.announce()

    # The callback for when a PUBLISH message is received from the server.
    def mqtt_callback_message(self, client, userdata, msg):

        if msg.topic in self.command_topics:
            payload = msg.payload.decode("utf-8")
            [device, switch, state_topic] = self.command_topics[msg.topic]
            print("calling device {}, switch {} with {}".format(
                device, switch, payload))
            if device.set_state({switch: payload}):
                self.mqtt_client.publish(state_topic, msg.payload)

        # ignore retained messages
        if msg.retain:
            return

        if msg.topic == "homeassistant/status":
            print("home assistant status message:", msg.topic)
            # report ourselves as available to home assistant

            if msg.payload == b'online':
                # re-report ourselves available to home assistant and report current state
                self.announce()

    def mqtt_callback_disconnect(self, client, userdata, rc):

        if rc != 0:
            print("Unexpected disconnection.")
