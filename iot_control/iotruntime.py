#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" IOT runtime class

"""

import time
import sys
import yaml
import iot_control.iot_devices.iotads1115
import iot_control.iot_devices.iotbme280
import iot_control.iot_devices.iotbh1750
import iot_control.iot_devices.iotraspigpio
import iot_control.iot_devices.iotcommandswitch
import iot_control.backends.influx
import iot_control.backends.mqtthass
from iot_control.iotfactory import IoTFactory


class IoTRuntime:
    """ this is the runtime class that will load the setup
        and put backends and sensors together and runs the
        main loop
    """
    backends = []
    devices = []
    update_intervall = 60

    def __init__(self, configfile: str):
        with open(configfile, 'r') as stream:
            try:
                self.conf = yaml.load(stream, Loader=yaml.SafeLoader)
            except yaml.YAMLError as exc:
                print(exc)
                print("Unable to parse configuration file {}".format(configfile))
                sys.exit(1)
        # first: build backends
        for backend in self.conf["backends"]:
            backend_cfg = self.conf["backends"][backend]
            try:
                self.backends.append(IoTFactory.create_backend(
                    backend, config=backend_cfg))
            except Exception as exception:
                print("error creating backend: {}".format(exception))
        sys.stdout.flush()
        # second: register devices with backend
        for device in self.conf["devices"]:
            device_cfg = self.conf["devices"][device]
            print(device_cfg)
            try:
                real_device = IoTFactory.create_device(
                    device, config=device_cfg)
                print(real_device)
                self.devices.append(real_device)
                for backend in self.backends:
                    backend.register_device(real_device)
            except Exception as exception:
                print("error creating device: {}".format(exception))
        sys.stdout.flush()
        for backend in self.backends:
            backend.announce()
        sys.stdout.flush()

    def set_intervall(self, new_intervall: int):
        """ sets the intervall between two readings of the sensors

        Args:
            new_intervall (int): the new interval in seconds between
            readings of the sensors
        """
        self.update_intervall = new_intervall

    def loop_forever(self):
        """ the main loop of the runtime
        """
        while True:
            for device in self.devices:
                data = device.read_data()
                for backend in self.backends:
                    backend.workon(device, data)
            time.sleep(self.update_intervall)
