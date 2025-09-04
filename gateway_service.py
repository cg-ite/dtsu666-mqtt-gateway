import asyncio
import logging
import json
import minimalmodbus
import paho.mqtt.client as mqtt

from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.server import StartAsyncSerialServer
from config import load_config
from dtsu666_constants import *

CONFIG_FILE = "config.json"
config = load_config(CONFIG_FILE)
logging.basicConfig(level=logging.basicConfig(level=config['logging']['level']))

# ---------------------------------------------------------------------------
# Konfiguration laden
# ---------------------------------------------------------------------------

MQTT_BROKER = config["mqtt"]["broker"]
MQTT_PORT = config["mqtt"]["port"]
MQTT_TOPIC_PREFIX = config["mqtt"]["topic_prefix"]

READER_PORT = config["reader"]["serial_port"]
READER_SLAVE_ID = config["reader"]["slave_id"]
READER_BAUD = config["reader"]["baudrate"]
READ_INTERVAL = config["reader"]["interval_sec"]

EMU_PORT = config["emulator"]["serial_port"]
EMU_SLAVE_ID = config["emulator"]["slave_id"]
EMU_BAUD = config["emulator"]["baudrate"]

REG = config["registers"]

# ---------------------------------------------------------------------------
# MQTT Client
# ---------------------------------------------------------------------------
mqtt_client = mqtt.Client()

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
def read_registers_once():
    instrument = minimalmodbus.Instrument(READER_PORT, READER_SLAVE_ID)
    instrument.serial.baudrate = READER_BAUD
    instrument.serial.timeout = 1

    try:
        logger.info(f"MeterType={meter_type} V={voltage} A={current} P={power}")

        mqtt_client.publish(f"{MQTT_TOPIC_PREFIX}/{TOTAL_REACTIVE_POWER}", power)

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

    await StartAsyncSerialServer(
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

    logging.getLogger(__name__).addHandler(logging.NullHandler())
    logger = logging.getLogger(__name__)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Beendet.")
