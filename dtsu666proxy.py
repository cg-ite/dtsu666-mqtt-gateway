#!/usr/bin/env python3
"""
dtsu666-mqtt-gateway
-------------------------------------------------
Acts as a Modbus RTU-to-RTU proxy for the DTSU666 energy meter.

- Listens on one serial port as a Modbus RTU server (for inverter).
- Forwards requests to another serial port connected to the DTSU666.
- Publishes every read operation and result to MQTT.

Author: Christian Günther cg-ite@gmx.de
License: GPLv3
"""

import json
import logging
import asyncio
from datetime import datetime

import paho.mqtt.client as mqtt
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.datastore import ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.server import StartAsyncSerialServer
from pymodbus.datastore.remote import RemoteSlaveContext
from pymodbus.datastore import ModbusDeviceContext, ModbusServerContext

from pymodbus.exceptions import ModbusException
#from pymodbus.constants import Defaults

from config import load_config

# --------------------------------------------------------------------------- #
# Logging configuration
# --------------------------------------------------------------------------- #
logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)
log = logging.getLogger("dtsu666-proxy")

# --------------------------------------------------------------------------- #
# MQTT Reporting DataBlock
# --------------------------------------------------------------------------- #
class MqttReportingDataBlock(ModbusSequentialDataBlock):
    """
    DataBlock for Modbus RTU server that forwards requests to another Modbus device
    and publishes every read to MQTT.
    """

    def __init__(self, mqtt_client, topic_prefix, reader_client, slave_id):
        super().__init__(0, [0] * 0x4000)
        self.mqtt_client = mqtt_client
        self.topic_prefix = topic_prefix
        self.reader = reader_client
        self.slave_id = slave_id

    async def getValues(self, address, count=1):
        """
        Called when Modbus master (inverter) reads registers from this server.
        We'll forward the request to the DTSU666 and publish results to MQTT.
        """
        try:
            rr = await self.reader.read_holding_registers(address, count, slave=self.slave_id)
            if not rr or rr.isError():
                log.warning(f"Read error from DTSU666 @ {address}")
                return [0] * count

            values = rr.registers
            payload = {
                "timestamp": datetime.now().isoformat(),
                "address": address,
                "values": values,
            }
            topic = f"{self.topic_prefix}/read/{address}"
            self.mqtt_client.publish(topic, json.dumps(payload))
            log.info(f"MQTT publish {topic}: {values}")
            return values

        except ModbusException as e:
            log.error(f"Modbus read exception: {e}")
            return [0] * count

        except Exception as e:
            log.exception(f"Error forwarding read: {e}")
            return [0] * count

# --------------------------------------------------------------------------- #
# Main async function
# --------------------------------------------------------------------------- #
async def main():
    cfg = load_config("config.json")

    # MQTT setup
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(cfg["mqtt"]["username"], cfg["mqtt"]["password"])
    mqtt_client.connect(cfg["mqtt"]["host"], cfg["mqtt"]["port"], 60)
    mqtt_client.loop_start()

    # Serial client to DTSU666
    reader_client = AsyncModbusSerialClient(
        method="rtu",
        port=cfg["reader"]["port"],
        baudrate=cfg["reader"]["baudrate"],
        parity=cfg["reader"]["parity"],
        stopbits=cfg["reader"]["stopbits"],
        bytesize=8,
        timeout=cfg["reader"]["timeout"]
    )

    await reader_client.connect()
    if not reader_client.connected:
        log.error("Could not connect to DTSU666 serial port.")
        return

    # Create Modbus RTU server that the inverter connects to
    datablock = MqttReportingDataBlock(
        mqtt_client,
        cfg["mqtt"]["topic_prefix"],
        reader_client.protocol,
        cfg["slave"]["id"]
    )

    store = ModbusDeviceContext(hr=datablock, zero_mode=True)
    context = ModbusServerContext(slaves={cfg["slave"]["id"]: store}, single=False)

    log.info("Starting DTSU666 MQTT RTU Proxy ...")
    log.info(f"Reader port: {cfg['reader']['port']} → Emulator port: {cfg['emulator']['port']}")

    await StartAsyncSerialServer(
        context=context,
        port=cfg["emulator"]["port"],
        framer="rtu",
        baudrate=cfg["emulator"]["baudrate"],
        stopbits=cfg["emulator"]["stopbits"],
        bytesize=8,
        parity=cfg["emulator"]["parity"]
    )

# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Stopping DTSU666 MQTT RTU Proxy.")
