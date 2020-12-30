#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" definitions for an BME280 sensor
"""

from typing import Dict
import smbus2
import bme280
from iot_control.iotdevicebase import IoTDeviceBase
from iot_control.iotfactory import IoTFactory


@IoTFactory.register_device("bme280")
class IoTbme280(IoTDeviceBase):
    """ BME280 sensor class
    """

    def __init__(self, **kwargs):
        super().__init__()
        setupdata = kwargs.get("config")
        self.conf = setupdata
        self.port = setupdata["port"]
        self.address = setupdata["i2c_address"]

    def read_data(self) -> Dict:
        """ read data """
        bus = smbus2.SMBus(self.port)
        calibration_params = bme280.load_calibration_params(
            bus, self.address)
        data = bme280.sample(bus, self.address, calibration_params)
        val = {
            "temperature": "{:.1f}".format(data.temperature),
            "humidity": "{:.1f}".format(data.humidity),
            "pressure": "{:.1f}".format(data.pressure)
        }
        bus.close()
        return val

    def sensor_list(self) -> list:
        return ["temperature", "humidity", "pressure"]

    def set_state(self, _) -> bool:
        """ nothing can be set here """

    def shutdown(self, _) -> None:
        """ nothing to do """
