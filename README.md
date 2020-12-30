# Control your IoT devices

This project provides a framework to easily connect IoT devices (sensors and switches) with different backends. It allows to include more backends and devices.

## Supported devices:
* [BME280 sensor](https://www.amazon.de/Adafruit-Temperature-Humidity-Pressure-ADA2652/dp/B013W0RR6Y): humidity, air pressure, temperature
* [ADS1115 sensor](https://www.amazon.de/Adafruit-ads1115-16-Bit-Channel-programmierbar-Verst%C3%A4rken/dp/B00QIW4MGW/ref=sr_1_2?__mk_de_DE=%C3%85M%C3%85%C5%BD%C3%95%C3%91&dchild=1&keywords=ads1115+adafruit&qid=1609321159&sr=8-2): 
* [BH1750](https://www.amazon.de/AZDelivery-GY-302-Helligkeitsensor-Arduino-Raspberry/dp/B07QBPRZH1/ref=sr_1_1_sspa?dchild=1&keywords=bh1750&qid=1609321202&sr=8-1-spons&psc=1&spLa=ZW5jcnlwdGVkUXVhbGlmaWVyPUEyVkI3SDNHSzFYRFFRJmVuY3J5cHRlZElkPUEwNjExNjQwM1NBR1dFMVJSNE01UyZlbmNyeXB0ZWRBZElkPUEwOTg0NzIxVklHUFVDSE8zQkIzJndpZGdldE5hbWU9c3BfYXRmJmFjdGlvbj1jbGlja1JlZGlyZWN0JmRvTm90TG9nQ2xpY2s9dHJ1ZQ==): illuminance
* [Raspberry PI GPIO switches](https://learn.sparkfun.com/tutorials/raspberry-gpio/all): drive GPIO pins on the raspberry pi. To actually drive the pins you need to use the mqtt-hass backend.

## Supported backends:

Backends can set and read states if the functionality of the software used provides this. Pure database backends like influx will only store the values from the sensors.

* [Home Assistant with MQTT discovery](https://www.home-assistant.io/docs/mqtt/discovery/): works for sensors and switches
* [InfluxDB](https://en.wikipedia.org/wiki/InfluxDB): works for sensors only, will ignore switches
