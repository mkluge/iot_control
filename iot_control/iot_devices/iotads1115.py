#!/usr/bin/python
# -*- coding: utf-8 -*-

""" definitions for an ADS115 analog digital converter
"""

from typing import Dict
from time import sleep
from iot_control.iotdevicebase import IoTDeviceBase
from iot_control.iotfactory import IoTFactory
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn



@IoTFactory.register_device("ads1115")
class IoTads1115(IoTDeviceBase):
    """ ADS1115 sensor class
    """

    def __init__(self, **kwargs):
        super().__init__()
        setupdata = kwargs.get("config")
        self.conf = setupdata

    def read_data(self) -> Dict:
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        value = 0
        while not value:
            chan = AnalogIn(ads, ADS.P0)
            value = chan.value
        value = float(value)*4.096/32768.0
        val = {
            "feuchte": "{:.2f}".format(value),
        }
        return val

    def sensor_list(self) -> list:
        return ["voltage"]

    def set_state(self, _) -> bool:
        """ nothing can be set here """

    def shutdown(self, _) -> None:
        """ nothing to do """
