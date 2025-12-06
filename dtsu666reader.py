#!/usr/bin/env python3
import argparse
import asyncio
import logging
import signal
from pymodbus.pdu.register_message import ReadHoldingRegistersResponse
import pymodbus.client as ModbusClient
from pymodbus import (
    FramerType,
)

from config import load_config
from dtsu666_constants import FOUR_WIRE_KEYS, REGISTERS

CONFIG_FILE = "config.json"

# --------------------------------------------------------------------------- #
# Logging configuration
# --------------------------------------------------------------------------- #
logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)
log = logging.getLogger("dtsu666reader")

class Dtsu666Reader:
    """Reader class for Chint DTSU666 energy meter"""

    def __init__(self, cfg):
        self.device_id = cfg["device"]["id"]
        self.instrument = ModbusClient.AsyncModbusSerialClient(
            framer=FramerType.RTU,
            port=cfg["reader"]["port"],
            timeout=cfg["reader"]["timeout"],
            baudrate=cfg["reader"]["baudrate"],
            parity=cfg["reader"]["parity"],
            stopbits=cfg["reader"]["stopbits"],
            bytesize=8,
            # retries=3,
            # handle_local_echo=False,
        )

    async def connect(self):
        await self.instrument.connect()
        if not self.instrument.connected:
            log.error("Could not connect to DTSU666 serial port.")
            return
        log.info("Connected to DTSU666 serial port.")

    def close(self):
        self.instrument.close()
        log.info("Close connection to DTSU666 serial port.")

    async def read_values(self, count=1):
        """Reads the most important values from the DTSU666"""
        data = {}
        for address in FOUR_WIRE_KEYS:
            try:
                spec = REGISTERS[address]
                rr = await self.instrument.read_holding_registers(address,
                                                                  count=spec["words"],
                                                                  device_id=self.device_id)

                if not isinstance(rr, ReadHoldingRegistersResponse):
                    continue
                if not rr or rr.isError():
                    log.warning(f"Read error from DTSU666 @ {address}")
                    return [0] * count

                raw = self.instrument.convert_from_registers(
                    rr.registers, word_order='big',
                    data_type=self.instrument.DATATYPE.FLOAT32,
                    string_encoding="ascii")
                data[address] = raw * spec["factor"]
            except Exception as e:
                print(f"Read error {address}: {e}")
                data[address] = None
        return data

async def main():
    """Reads the consumption data of a dtsu666 once"""

    # load defaults from config.json
    config = load_config()

    parser = argparse.ArgumentParser(
        description=(
            "Chint DTSU666 Modbus Reader: "
            "A command line tool for testing the Modbus connection "
            "to a DTSU666 energy meter"
        )
    )

    reader = Dtsu666Reader(
        cfg=config
    )

    await reader.connect()
    values = await reader.read_values()
    if values:
        for k, v in values.items():
            print(f"{k:30}: {v:.3f}")
    reader.close()

def raise_graceful_exit(*_args):
    """Enters shutdown mode"""
    log.info("Receiving shutdown signal now.")
    raise SystemExit

if __name__ == "__main__":
    try:
        signal.signal(signal.SIGINT, raise_graceful_exit)
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Exit.")
