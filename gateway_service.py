import asyncio
import logging
import json
import paho.mqtt.client as mqtt

from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.server.async_io import StartSerialServer

from config import load_config
from dtsu666_constants import REGISTERS, VOLTAGE_PHASE_A, CURRENT_PHASE_A, TOTAL_IMPORT_ENERGY, TOTAL_EXPORT_ENERGY
from dtsu666reader import Dtsu666Reader

CONFIG_FILE = "config.json"
config = load_config(CONFIG_FILE)
logging.basicConfig(level=config['logging']['level'])
logger = logging.getLogger("dtsu666-gateway")

# ---------------------------------------------------------------------------
# Konfiguration laden
# ---------------------------------------------------------------------------

MQTT_BROKER = config["mqtt"]["broker"]
MQTT_PORT = config["mqtt"]["port"]
MQTT_USERNAME = config["mqtt"]["username"]
MQTT_PASSWORD = config["mqtt"]["password"]
MQTT_TOPIC_PREFIX = config["mqtt"]["topic_prefix"]

READER_PORT = config["dtsu666"]["port"]
READER_SLAVE_ID = config["dtsu666"]["slave_id"]
READER_BAUD = config["dtsu666"]["baudrate"]
READ_INTERVAL = config["dtsu666"]["interval_sec"]

EMU_PORT = config["emulator"]["port"]
EMU_SLAVE_ID = config["emulator"]["slave_id"]
EMU_BAUD = config["emulator"]["baudrate"]

REG = config["registers"]

# ---------------------------------------------------------------------------
# MQTT Client
# ---------------------------------------------------------------------------
mqtt_client = mqtt.Client()
if MQTT_USERNAME:
    mqtt_client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)

shared_values = {
    "meter_type": 0,
    "voltage": 0.0,
    "current": 0.0,
    "power": 0.0
}

def on_connect(client, userdata, flags, rc):
    logger.info("MQTT connected with result code %s", rc)
    client.subscribe(f"{MQTT_TOPIC_PREFIX}/#")

def on_message(client, userdata, msg):
    topic = msg.topic.split("/")[-1]
    try:
        val = float(msg.payload.decode())
    except ValueError:
        return
    if topic in shared_values:
        shared_values[topic] = val

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# ---------------------------------------------------------------------------
# Reader Task
# ---------------------------------------------------------------------------
reader = Dtsu666Reader(READER_PORT, READER_BAUD, READER_SLAVE_ID)

def read_registers_once():
    try:
        values = reader.read_values()
        # Beispielwerte ins Log
        logger.debug(
            "Some DTSU reading for debugging: "
            f"{VOLTAGE_PHASE_A}={values.get(VOLTAGE_PHASE_A)} "
            f"{CURRENT_PHASE_A}={values.get(CURRENT_PHASE_A)} "
            f"{TOTAL_IMPORT_ENERGY}={values.get(TOTAL_IMPORT_ENERGY)} "
            f"{TOTAL_EXPORT_ENERGY}={values.get(TOTAL_EXPORT_ENERGY)} "
        )

        # MQTT Publishes
        for key, val in values.items():
            if val is not None:
                mqtt_client.publish(f"{MQTT_TOPIC_PREFIX}/{key}", val)

        # shared_values für Emulator updaten
        shared_values = values

    except Exception as e:
        logger.error("Fehler beim Lesen: %s", e)

async def reader_task():
    while True:
        read_registers_once()
        mqtt_client.loop(0.1)
        await asyncio.sleep(READ_INTERVAL)

# ---------------------------------------------------------------------------
# Emulator – holt Werte aus MQTT
# ---------------------------------------------------------------------------
class MQTTSynchronizedDataBlock(ModbusSequentialDataBlock):
    def __init__(self):
        super().__init__(0, [0] * 0x3000)

    def getValues(self, address, count=1):
        if address == REG["meter_type"]:
            return [int(shared_values["meter_type"])]
        elif address == REG["voltage"]:
            return [int(shared_values["voltage"] * 10)]
        elif address == REG["current"]:
            return [int(shared_values["current"] * 100)]
        elif address == REG["power"]:
            return [int(shared_values["power"])]
        return [0] * count

async def run_emulator():
    store = ModbusSlaveContext(
        hr=MQTTSynchronizedDataBlock(),
        zero_mode=True
    )
    context = ModbusServerContext(slaves={EMU_SLAVE_ID: store}, single=False)

    await StartSerialServer(
        context=context,
        port=EMU_PORT,
        framer="rtu",
        baudrate=EMU_BAUD,
        stopbits=1,
        bytesize=8,
        parity="N"
    )

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main():
    task1 = asyncio.create_task(reader_task())
    task2 = asyncio.create_task(run_emulator())
    while True:
        mqtt_client.loop(0.1)
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Beendet.")
