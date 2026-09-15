#!/bin/bash

docker build -t mqtt-influx-bridge-solar:latest .
docker stop mqtt-influx-bridge-solar
docker rm mqtt-influx-bridge-solar
sh run.sh
