#!/usr/bin/python
# -*- coding: utf-8 -*-

""" definitions for GPIO pins on a raspberry pi
"""

from typing import Dict
import os
from iot_control.iotdevicebase import IoTDeviceBase, IoTConfigError
from iot_control.iotfactory import IoTFactory


@IoTFactory.register_device("command-switch")
class IoTcommandswitch(IoTDeviceBase):
    """ running shell commands if the switch is triggered
    """

    last_state = {}
    on_cmds = {}
    off_cmds = {}

    def __init__(self, **kwargs):
        super().__init__()
        setupdata = kwargs.get("config")
        self.conf = setupdata
        for switch in self.conf["names"]:
            sw_cfg = self.conf["names"][switch]
            if not "on_command" in sw_cfg:
                raise IoTConfigError(
                    "on_command should be set for switch {}".format(switch))
            if not "off_command" in sw_cfg:
                raise IoTConfigError(
                    "off_command should be set for switch {}".format(switch))
            self.on_cmds[switch] = sw_cfg["on_command"]
            self.off_cmds[switch] = sw_cfg["off_command"]
            # assume off as initial state
            self.last_state[switch] = False

    def read_data(self) -> Dict:
        """ read data """
        val = {}
        for name in self.on_cmds:
            if self.last_state[name]:
                payload = self.conf["payload_on"]
            else:
                payload = self.conf["payload_off"]
            val[name] = payload
        return val

    def sensor_list(self) -> list:
        return self.on_cmds.keys()

    def set_state(self, messages: Dict) -> bool:
        for msg in messages:
            if msg in self.on_cmds.keys():
                if messages[msg] == self.conf["payload_on"]:
                    os.system(self.on_cmds[msg])
                else:
                    os.system(self.off_cmds[msg])
        return True

    def shutdown(self, _) -> None:
        """ nothing to do """
