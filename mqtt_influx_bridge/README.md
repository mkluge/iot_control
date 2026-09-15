# MQTT to InfluxDB bridge on Synology

The container reads `/config/config.json` when it starts. The local
`config.json` carries the settings previously embedded in `bridge.py`. On a
fresh checkout, copy `config.example.json` to `config.json` and fill in the
real values. Check both the MQTT and InfluxDB host addresses from inside the
container's network. The real config is ignored by Git and excluded from the
Docker build context.

From this directory on the Synology:

```sh
docker build -t mqtt-influx-bridge:latest .
sh run.sh
```

The script starts a detached container named `mqtt-influx-bridge` with
automatic restart. It only makes outbound connections, so no ports need to
be published. You can pass an absolute config path, for example
`sh run.sh /volume1/docker/mqtt-influx-bridge/config.json`.
Use `docker logs -f mqtt-influx-bridge` to inspect it.

After changing the JSON file, run `docker restart mqtt-influx-bridge`.
After changing the code, rebuild and recreate the container:

```sh
docker build -t mqtt-influx-bridge:latest .
docker stop mqtt-influx-bridge
docker rm mqtt-influx-bridge
sh run.sh
```
