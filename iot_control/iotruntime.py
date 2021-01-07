#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" IOT runtime class

"""

import time
import sys
import logging
import yaml
import iot_control.iot_devices.iotads1115
import iot_control.iot_devices.iotbme280
import iot_control.iot_devices.iotbh1750
import iot_control.iot_devices.iotraspigpio
import iot_control.iot_devices.iotcommandswitch
import iot_control.backends.influx
import iot_control.backends.mqtthass
from iot_control.iotfactory import IoTFactory


class IoTRuntime:
    """ this is the runtime class that will load the setup
        and put backends and sensors together and runs the
        main loop
    """
    backends = []
    devices = []
    update_intervall = 60

    def __init__(self, configfile: str, log_level=logging.WARNING):

        self.logger = logging.getLogger('iot_control')
        self.logger.setLevel(log_level)
        filehandler = logging.FileHandler('iot_control.log')
        filehandler.setLevel(log_level)
        self.logger.addHandler(filehandler)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        filehandler.setFormatter(formatter)
        self.logger.addHandler(filehandler)
        # logger.debug('Debug-Nachricht')
        # logger.info('Info-Nachricht')
        # logger.warning('Warnhinweis')
        # logger.error('Fehlermeldung')
        # logger.critical('Schwerer Fehler')

        self.logger.info("loading config file %s", configfile)
        with open(configfile, 'r') as stream:
            try:
                self.conf = yaml.load(stream, Loader=yaml.SafeLoader)
            except yaml.YAMLError as exc:
                self.logger.critical(exc)
                self.logger.critical(
                    "Unable to parse configuration file %s", configfile)
                sys.exit(1)
        # first: build backends
        for backend in self.conf["backends"]:
            self.logger.info("creating backend %s", backend)
            backend_cfg = self.conf["backends"][backend]
            try:
                self.backends.append(IoTFactory.create_backend(
                    backend, config=backend_cfg))
            except Exception as exception:
                self.logger.error(
                    "error creating backend: %s", exception)
        sys.stdout.flush()
        if not self.backends:
            self.logger.critical("no backends available")
            sys.exit(1)
            # second: register devices with backend
        for device in self.conf["devices"]:
            self.logger.info("creating device %s", device)
            device_cfg = self.conf["devices"][device]
            try:
                real_device = IoTFactory.create_device(
                    device, config=device_cfg)
                self.devices.append(real_device)
                for backend in self.backends:
                    backend.register_device(real_device)
            except Exception as exception:
                self.logger.error(
                    "error creating device: %s", exception)
        for backend in self.backends:
            backend.announce()

    def set_intervall(self, new_intervall: int):
        """ sets the intervall between two readings of the sensors

        Args:
            new_intervall (int): the new interval in seconds between
            readings of the sensors
        """
        self.update_intervall = new_intervall

    def loop_forever(self):
        """ the main loop of the runtime
        """
        self.logger.info(
            "starting main loop with %d seconds intervall", int(self.update_intervall))
        try:
          while True:
              for device in self.devices:
                  data = device.read_data()
                  for backend in self.backends:
                      backend.workon(device, data)
              time.sleep(self.update_intervall)
        except KeyboardInterrupt:
            self.logger.error( "Keyboard interrupt" )
        except:
            self.logger.error( "unexpected error" )

        for backend in self.backends:
            backend.shutdown()
        
            
