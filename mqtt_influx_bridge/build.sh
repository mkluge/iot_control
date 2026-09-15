#!/bin/bash

docker build -t mqtt-influx-bridge:latest .
docker stop mqtt-influx-bridge
docker rm mqtt-influx-bridge
sh run.sh
