#!/usr/bin/python
# -*- coding: utf-8 -*-

""" definitions for GPIO pins on a raspberry pi
"""

from typing import Dict
import os
import unittest
from iot_control.iotdevicebase import IoTDeviceBase, IoTConfigError
from iot_control.iotfactory import IoTFactory


@IoTFactory.register_device("command_switch")
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
        if not "switches" in setupdata:
            raise IoTConfigError(
                "missing switches in setup data")
        for switch in self.conf["switches"]:
            sw_cfg = self.conf["switches"][switch]
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
        for switch in self.on_cmds:
            if self.last_state[switch]:
                payload = self.conf["payload_on"]
            else:
                payload = self.conf["payload_off"]
            val[switch] = payload
        return val

    def sensor_list(self) -> list:
        return self.on_cmds.keys()

    def set_state(self, messages: Dict) -> bool:
        for msg in messages:
            if msg in self.on_cmds.keys():
                if messages[msg] == self.conf["payload_on"]:
                    os.system(self.on_cmds[msg])
                    self.last_state[msg] = True
                else:
                    os.system(self.off_cmds[msg])
                    self.last_state[msg] = False
        return True

    def shutdown(self, _) -> None:
        """ nothing to do """


class IoTcommandswitchTest(unittest.TestCase):
    def test_missing_switches(self):
        config = {"off_command": 0}
        with self.assertRaises(IoTConfigError):
            f = IoTcommandswitch(config=config)

    def test_missing_on_command(self):
        config = {"switches": {"test": {"off_command": 0}}}
        with self.assertRaises(IoTConfigError):
            f = IoTcommandswitch(config=config)

    def test_missing_off_command(self):
        config = {"switches": {"test": {"on_command": 1}}}
        with self.assertRaises(IoTConfigError):
            f = IoTcommandswitch(config=config)


if __name__ == '__main__':
    unittest.main()
