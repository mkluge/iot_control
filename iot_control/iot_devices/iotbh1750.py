#!/usr/bin/python
# -*- coding: utf-8 -*-


""" definitions for an BH1750 sensor
"""

from typing import Dict
import smbus
from iot_control.iotdevicebase import IoTDeviceBase
from iot_control.iotfactory import IoTFactory


@IoTFactory.register_device("bh1750")
class IoTbh1750(IoTDeviceBase):
    """ BH1750 sensor class
    """

    def __init__(self, **kwargs):
        super().__init__()
        setupdata = kwargs.get("config")
        self.conf = setupdata
        self.port = setupdata["port"]
        self.address = setupdata["i2c_address"]

    def read_data(self) -> Dict:
        """ read data """
        bus = smbus.SMBus(self.port)
        # Start measurement at 1lx resolution. Time typically 120ms
        # Device is automatically set to Power Down after measurement.
        ONE_TIME_HIGH_RES_MODE_1 = 0x20
        # Read data from I2C interface
        data = bus.read_i2c_block_data(
            self.address, ONE_TIME_HIGH_RES_MODE_1)
        result = (data[1] + (256 * data[0])) / 1.2
        val = {
            "illuminance": "{:.1f}".format(result),
        }
        bus.close()
        return val

    def sensor_list(self) -> list:
        return ["illuminance"]

    def set_state(self, _) -> bool:
        """ nothing can be set here """

    def shutdown(self, _) -> None:
        """ nothing to do """
