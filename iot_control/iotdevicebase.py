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

    def __init__(self, **kwargs):
        """ Constructor """

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
