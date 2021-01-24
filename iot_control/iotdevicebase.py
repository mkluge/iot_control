#!/usr/bin/env python
# -*- coding: utf-8 -*-


""" device base class definition

"""

from abc import ABCMeta, abstractmethod
from typing import Dict


class IoTDeviceBase(metaclass=ABCMeta):
    """ base class for IoT device
    """

    # each thing will have a config dict
    conf = {}
    runtime = None

    def __init__(self, **kwargs):
        """ Constructor """

    def give_runtime_reference(self, runtime) -> None:
        """ initialize the reference to the runtime object. This is only needed for devices
        which want to schedule events by themselves. All others don't need to know about this one"""
        self.runtime = runtime

    @abstractmethod
    def read_data(self) -> Dict:
        """ Abstract method to read data """

    @abstractmethod
    def sensor_list(self) -> list:
        """ Lists all sensors on the device """

    @abstractmethod
    def set_state(self, messages: Dict) -> bool:
        """ Abstract method to set a new state """

    @abstractmethod
    def shutdown(self, data: Dict) -> None:
        """ Abstract method to shut down """


class IoTConfigError(Exception):
    """exception raised on a configuration error"""

    def __init__(self, msg="error in the config file"):
        super().__init__()
