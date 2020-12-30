#!/usr/bin/python
# -*- coding: utf-8 -*-

""" definitions for GPIO pins on a raspberry pi
"""

from typing import Dict
import RPi.GPIO as GPIO
from iot_control.iotdevicebase import IoTDeviceBase
from iot_control.iotfactory import IoTFactory


@IoTFactory.register_device("raspi-gpio")
class IoTraspigpio(IoTDeviceBase):
    """ Raspberry pi GPIO class
    """

    # stores mapping of names to pins
    names = {}

    def __init__(self, **kwargs):
        super().__init__()
        setupdata = kwargs.get("config")
        self.conf = setupdata
        GPIO.setmode(GPIO.BCM)  # GPIO Nummern statt Board Nummern
        GPIO.setwarnings(False)
        names_cfg = setupdata["names"]
        for name in names_cfg:
            cfg = names_cfg[name]
            pin = cfg["pin"]
            GPIO.setup(pin, GPIO.OUT)  # GPIO Modus zuweisen
            self.names[name] = pin

    def read_data(self) -> Dict:
        """ read data """
        val = {}
        for name in self.names:
            pin = self.names[name]
            if not GPIO.input(pin):
                payload = self.conf["payload_off"]
            else:
                payload = self.conf["payload_on"]
            val[name] = payload
        return val

    def sensor_list(self) -> list:
        return self.names.keys()

    def set_state(self, messages: Dict) -> bool:
        for msg in messages:
            if msg in self.names:
                pin = self.names[msg]
                GPIO.setup(pin, GPIO.OUT)
                if messages[msg] == self.conf["payload_on"]:
                    GPIO.output(pin, GPIO.HIGH)
                else:
                    GPIO.output(pin, GPIO.LOW)
        return True

    def shutdown(self, _) -> None:
        """ nothing to do """
