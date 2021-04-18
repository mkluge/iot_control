#!/usr/bin/python3
# -*- coding: utf-8 -*-

""" InfluxDB backend for iot_control
"""


import datetime
from typing import Dict
import logging
import influxdb
from iot_control.iotbackendbase import IoTBackendBase
from iot_control.iotdevicebase import IoTDeviceBase
from iot_control.iotfactory import IoTFactory


@IoTFactory.register_backend("influx")
class BackendInfluxDB(IoTBackendBase):
    """ the backend class

    Args:
        IoTBackendBase: the base class
    """
    devices = []
    json_templates = {}
    influx = None

    def __connect(self):
        self.logger.info("connecting to influxdb")
        self.influx = influxdb.InfluxDBClient(host=self.config['server'],
                                              port=self.config['port'],
                                              username=self.config['user'],
                                              password=self.config['password'],
                                              database=self.config['database'])


    def __init__(self, **kwargs):
        super().__init__()
        self.logger = logging.getLogger('iot_control')
        self.config = kwargs.get("config", None)

        self.__connect()

        list= [db['name'] for db in self.influx.get_list_database()]
        #list= self.influx.get_list_database()
        self.logger.debug( "Connected to InfluxDB %s:%s", self.config['server'], self.config['port'] )
        self.logger.debug( "    Existing databases:" )
        for l in list:
            self.logger.debug( "        '%s'", l )

        if self.config['database'] not in list:
            self.logger.info( "Create new Influx database '%s'", self.config['database'] )
            self.influx.create_database( self.config['database'] )
        else:
            self.logger.debug( "Influx database '%s' already present", self.config['database'] )


    def register_device(self, device: IoTDeviceBase) -> None:
        """ register a device with the backend
        """
        self.devices.append(device)

    def shutdown(self):
        self.logger.info("shutdown influxdb")
        self.influx.close()

    def workon(self, device: IoTDeviceBase, data: Dict):

        if None == self.influx:
            self.logger.info("Influx connection not present, try to reconnect '%s'", self.config['database'] )
            self.__connect()

        if not device in self.json_templates:
            self.logger.error("unknown device")
            return

        json_templates= self.json_templates[device]

        if None != self.influx:
            try:
                for entry in data:
                    # send to influx db
                    if entry in json_templates:
                        self.logger.debug("influx data for field %s with value %s",
                                        entry, data[entry])
                        template= json_templates[entry]
                        template[0]["time"] = "{}".format(datetime.datetime.utcnow())
                        template[0]["fields"][entry] = float( data[entry] )
                        print( "    ", template )
                        self.influx.write_points(template)
            except Exception as error:
                self.logger.info("Exception %s", error )
                self.influx = None

    def announce(self):
        for device in self.devices:

            json_templates= {}

            # is it a sensor or a switch
            if "sensors" in device.conf:
                # get list of sensors on device
                sensors = device.conf["sensors"]
                # create a state topic for everyone
                try:
                    sensor_cfg = device.conf["sensors"]
                    for sensor in sensors:
                        try:
                            self.logger.info(
                                "influx registering sensor %s", sensor)
                            sconf = sensor_cfg[sensor]
                            json_template = [
                                {
                                    "measurement": sconf["name"],
                                    "tags": {
                                        "source": sconf["unique_id"],
                                    },
                                    "fields": {
                                    }
                                },
                            ]
                            json_templates[sensor] = json_template
                        except Exception as exception:
                            self.logger.error("config for sensor %s wrong: %s",
                                              sensor, exception)
                except Exception as exception:
                    self.logger.error("error announcing sensor: %s", exception)
            else:
                # it is a switch
                # - not supported here
                pass

            # finally add device's state topics list to permanent list
            self.json_templates[device] = json_templates
