#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Dachgarten

"""

from iot_control.iotruntime import IoTRuntime

if __name__ == '__main__':

    # Creates a runtime that will run everything
    runtime = IoTRuntime("setup.yaml")
    runtime.set_intervall(60)
    runtime.loop_forever()
