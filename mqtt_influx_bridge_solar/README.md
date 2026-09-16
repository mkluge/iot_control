# SolarFlow MQTT to InfluxDB bridge on Synology

The container reads `/config/config.json` each time it starts. In this checkout,
the local `config.json` contains the settings previously embedded in `bridge.py`;
check and edit them for your Synology. On a fresh checkout, copy
`config.example.json` to `config.json` and fill in the real values. The real
config is ignored by Git and excluded from the Docker build context.

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

## Inspect all SolarFlow MQTT data

`mqtt_test.py` obtains the MQTT credentials in the same way as the bridge and
pretty-prints every retained or live message the broker permits the account to
see. It first requests the broker-wide `#` wildcard and falls back to the two
known SolarFlow account topic forms if the broker rejects that subscription.

Install the existing Python dependencies, then run it from this directory:

```sh
python3 -m pip install -r requirements.txt
python3 mqtt_test.py
```

Stop it with Ctrl-C, or make a time-limited capture (for example, 60 seconds):

```sh
python3 mqtt_test.py --seconds 60
```

Use `--config /path/to/config.json` to select another configuration. The script
prints connection metadata and payloads, but never prints the temporary MQTT
password. Non-JSON UTF-8 payloads are printed as strings and binary payloads as
base64 so no reachable message content is discarded.
