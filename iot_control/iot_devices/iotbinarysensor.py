#!/usr/bin/python
# -*- coding: utf-8 -*-

""" definitions for GPIO pins on a raspberry pi as binary sensors
"""

from typing import Dict
import RPi.GPIO as GPIO
import logging
from iot_control.iotdevicebase import IoTDeviceBase
from iot_control.iotfactory import IoTFactory


@IoTFactory.register_device("binary-sensor")
class IoTbinarysensor(IoTDeviceBase):
    """ binary sensor class to act upon an input GPIO pin on a Raspi
    """

    # stores mapping of binary sensors to pins
    sensors = {}
    
    # handle for a pending autooff event
    handle = None

    def __callback(self, pin, state, cfg):
        """ The real callback function actin upon a state change of one of the GPIO pins """
        print( "__callback:" )
        print( "    pin:", pin )
        print( "    state:", state )
        print( "    cfg:", cfg )

    def __init__(self, **kwargs):
        super().__init__()
        setupdata = kwargs.get("config")
        print("new IoTbinarysensor: ", setupdata)
        self.conf = setupdata
        GPIO.setmode(GPIO.BCM)  # GPIO Nummern statt Board Nummern
        GPIO.setwarnings(False)

        sensors_cfg = setupdata["binary-sensors"]

        def callback( pin ):
            """ Helper callback function providing all the interesting arguments that the stupid API of 
            GPIO.add_event_detect() doesn't like to give us"""
            #print( "callback on ", pin )
            for sensor in sensors_cfg:
                #print( "try sensor ", sensor )
                if "pin" in sensors_cfg[sensor] and sensors_cfg[sensor]["pin"] == pin:
                    self.__callback(pin, not GPIO.input(pin), sensors_cfg[sensor])

        for sensor in sensors_cfg:
            cfg = sensors_cfg[sensor]
            pin = cfg["pin"]
            if "device_class" in cfg:
                self.device_class = cfg["device_class"]
            else:
                self.device_class = None

            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # GPIO Modus zuweisen
            self.sensors[sensor] = pin

            GPIO.add_event_detect( pin, GPIO.BOTH, callback= callback, bouncetime=100 )

    def read_data(self) -> Dict:
        """ read data """
        val = {}
        for sensor in self.sensors:
            pin = self.sensors[sensor]
            if not GPIO.input(pin):
                payload = self.conf["payload_off"]
            else:
                payload = self.conf["payload_on"]
            val[sensor] = payload
        return val

    def sensor_list(self) -> list:
        return self.sensors.keys()

    def set_state(self, messages: Dict) -> bool:
        print( "IoTbinarysensor.set_state() cannot act on messages", messages)
        return False # True

    def shutdown(self, _) -> None:
        """ Don't need to clean up for input pins """
        for sensor in self.sensors:
            pin = self.sensors[sensor]
            #GPIO.output(pin, GPIO.LOW)
