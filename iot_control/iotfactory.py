#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" IoT Factory

"""

from typing import Callable
import logging
from iot_control.iotdevicebase import IoTDeviceBase
from iot_control.iotbackendbase import IoTBackendBase


class IoTFactory:
    """ The factory class for creating devices and backends"""

    # internal registry for device classes
    device_registry = {}
    # internal registry for backends
    backend_registry = {}

    @ classmethod
    def register_device(cls, name: str) -> Callable:
        """ Class method to register Executor class to the internal registry.
        """

        def inner_wrapper(wrapped_class: IoTDeviceBase) -> Callable:
            cls.device_registry[name] = wrapped_class
            return wrapped_class

        return inner_wrapper

    @ classmethod
    def create_device(cls, name: str, **kwargs) -> 'IoTDeviceBase':
        """ Factory command to create the device.
        """

        # if there is a '%' in the device class then ignore the remainder,
        # this allows multiple devices of the same class
        pos= name.find("%")
        if -1 != pos:
            name= name[0:pos]

        if name not in cls.device_registry:
            raise SystemExit(
                'device {} does not exist in the registry'.format(name))

        logger = logging.getLogger('iot_control')
        logger.info("creating device for class %s", name)
        device_class = cls.device_registry[name]
        device = device_class(**kwargs)
        return device

    @ classmethod
    def register_backend(cls, name: str) -> Callable:
        """ Class method to register Executor class to the internal registry.
        """

        def inner_wrapper(wrapped_class: IoTBackendBase) -> Callable:
            cls.backend_registry[name] = wrapped_class
            return wrapped_class

        return inner_wrapper

    @ classmethod
    def create_backend(cls, name: str, **kwargs) -> 'IoTBackendBase':
        """ Factory command to create the backend.
        """

        if name not in cls.backend_registry:
            raise SystemExit(
                'backend class {} does not exist in the registry'.format(name))

        logger = logging.getLogger('iot_control')
        logger.info("creating backend for class %s", name)
        backend_class = cls.backend_registry[name]
        backend = backend_class(**kwargs)
        return backend
