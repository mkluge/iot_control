#!/usr/bin/env python
# -*- coding: utf-8 -*-


""" backend base class definition

"""

from abc import ABCMeta, abstractmethod
from typing import Dict
from iot_control.iotdevicebase import IoTDeviceBase


class IoTBackendBase(metaclass=ABCMeta):
    """ base class for IoT backend
    """

    # each thing will have a config dict
    conf = {}

    def __init__(self, **kwargs):
        """ Constructor """

    @abstractmethod
    def workon(self, thing: IoTDeviceBase, data: Dict) -> None:
        """ Abstract method to work on a sensors data """

    @abstractmethod
    def shutdown(self) -> None:
        """ Abstract method to shut down """

    @abstractmethod
    def register_device(self, device: IoTDeviceBase) -> None:
        """ Abstract method to register a device """
