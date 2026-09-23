# SolarFlow MQTT to InfluxDB bridge on Synology

The container reads `/config/config.json` each time it starts and writes to InfluxDB 2 using token authentication. In this checkout,
the local `config.json` contains the settings previously embedded in `bridge.py`;
check and edit them for your Synology. On a fresh checkout, copy
`config.example.json` to `config.json` and fill in the real values. The `influxdb` section requires `url`, `org`, `bucket`, `token`, and `measurement`. Use a dedicated write-only token for the configured bucket. The real config is ignored by Git and excluded from the Docker build context.

From this directory on the Synology, build and start the container:

```sh
# On a fresh checkout only: cp config.example.json config.json
# Edit config.json before starting.
docker build -t mqtt-influx-bridge-solar:latest .
sh run.sh
```

You can also pass an absolute config path: `sh run.sh /volume1/docker/solarflow/config.json`.
The script starts a detached container named `mqtt-influx-bridge-solar` with
automatic restart. The app only makes outbound connections, so no ports need
to be published. Use `docker logs -f mqtt-influx-bridge-solar` to inspect it.
After changing the JSON file, restart the container with
`docker restart mqtt-influx-bridge-solar` to load the new values.

After changing `bridge.py`, rebuild the image and recreate the container:

```sh
docker build -t mqtt-influx-bridge-solar:latest .
docker stop mqtt-influx-bridge-solar
docker rm mqtt-influx-bridge-solar
sh run.sh
```
