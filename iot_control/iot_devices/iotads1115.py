#!/usr/bin/python
# -*- coding: utf-8 -*-

""" definitions for an ADS115 analog digital converter
"""

from typing import Dict
from iot_control.iotdevicebase import IoTDeviceBase
from iot_control.iotfactory import IoTFactory
from iot_control.iot_devices.external.ADS1x15 import ADS1115


@IoTFactory.register_device("ads1115")
class IoTads1115(IoTDeviceBase):
    """ ADS1115 sensor class
    """

    def __init__(self, **kwargs):
        super().__init__()
        setupdata = kwargs.get("config")
        self.conf = setupdata
        # Import the ADS1115 module.
        self.adc = ADS1115()

    def read_data(self) -> Dict:
        """ read data """
        # Start ADC conversions on channel 0
        self.adc.start_adc(0, gain=1)
        value = self.adc.get_last_result()
        self.adc.stop_adc()
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
