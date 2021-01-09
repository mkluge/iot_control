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

    def __init__(self, **kwargs):
        super().__init__()
        self.logger = logging.getLogger('iot_control')
        config = kwargs.get("config", None)
        self.config = config
        self.logger.info("connecting to influxdb")
        self.influx = influxdb.InfluxDBClient(host=config['server'],
                                              port=config['port'],
                                              username=config['user'],
                                              password=config['password'],
                                              database=config['database'])
        list= [db['name'] for db in self.influx.get_list_database()]
        #list= self.influx.get_list_database()
        self.logger.debug( "Connected to InfluxDB %s:%s", config['server'], config['port'] )
        self.logger.debug( "    Existing databases:" )
        for l in list:
            self.logger.debug( "        '%s'", l )

        if config['database'] not in list:
            self.logger.info( "Create new Influx database '%s'", config['database'] )
            self.influx.create_database( config['database'] )
        else:
            self.logger.debug( "Influx database '%s' already present", config['database'] )
    
  
    def register_device(self, device: IoTDeviceBase) -> None:
        """ register a device with the backend
        """
        self.devices.append(device)

    def shutdown(self):
        self.logger.info("shutdown influxdb")
        #self.influx.close( `) ## apparently there is no 'close()'???

    def workon(self, thing: IoTDeviceBase, data: Dict):
        for entry in data:
            # send to influx db
            if entry in self.json_templates:
                self.logger.debug("influx data for field %s with value %s",
                                  entry, data[entry])
                template = self.json_templates[entry]
                template[0]["time"] = "{}".format(datetime.datetime.utcnow())
                template[0]["fields"][entry] = data[entry]
                self.influx.write_points(template)

    def announce(self):
        for device in self.devices:
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
                            self.json_templates[sensor] = json_template
                        except Exception as exception:
                            self.logger.error("config for sensor %s wrong: %s",
                                              sensor, exception)
                except Exception as exception:
                    self.logger.error("error announcing sensor: %s", exception)
            else:
                # it is a switch
                # - not supported here
                pass
