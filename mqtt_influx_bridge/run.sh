#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
config_file=${1:-"$script_dir/config.json"}

if [ ! -f "$config_file" ]; then
    printf 'Config file not found: %s\n' "$config_file" >&2
    exit 1
fi

config_dir=$(CDPATH= cd -- "$(dirname -- "$config_file")" && pwd)
config_file=$config_dir/$(basename -- "$config_file")

docker run -d \
    --name mqtt-influx-bridge \
    --restart unless-stopped \
    --mount "type=bind,source=$config_file,target=/config/config.json,readonly" \
    mqtt-influx-bridge:latest
