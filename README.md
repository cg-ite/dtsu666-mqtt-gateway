# dtsu666-mqtt-gateway
A lightweight Python-based gateway that connects a DTSU666 energy meter via Modbus RTU to MQTT and Home Assistant.

It periodically reads measurement data from the DTSU666 via Modbus RTU and publishes it to configurable MQTT topics, making the data easily accessible for Home Assistant and other IoT platforms.
In addition, the gateway includes an optional Modbus emulator, which can serve the MQTT data to a connected inverter or other Modbus client.

## Why another project?
I have a Qcells Q.VOLT-P5 inverter that only sends consumption data to the Qcells website every 5 minutes. This interval is too long for me. The inverter uses a DTSU666 as an information source, which is connected as a slave via Modbus RTU.

Therefore, I use the project to read the DTSU666 and send the data to my MQTT server. At the same time, I also send the data to the inverter by emulating the DTSU666 with this project.

My goal is to get the consumption data into my Home Assistant server.

## Features
- Reads values from a DTSU666 energy meter via Modbus RTU
- Publishes data to MQTT topics in JSON format
- Optional Modbus server emulation to serve MQTT data to inverters
- Configurable via `config.json`
- Designed to run as a background service with `systemd`

## References
This project is based on:
- https://github.com/elfabriceu/DTSU666-Modbus
- https://github.com/ChrisSiedler/dtsu666-Emulator/
- https://github.com/runesl/dtsu666mqtt
- https://github.com/johann-CH/ESP32_DTSU666_Modbus_MQTT_HA_Integration
- https://github.com/incub77/solis2mqtt


Other usefull projects:
- https://github.com/RafAustralia/Chint-DTSU666-20-modbus
- https://github.com/emavap/DTSU666-H-HA/

Big thank you all for your great work!

## License
GPLv3