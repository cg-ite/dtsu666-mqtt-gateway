#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import datetime
import logging
import struct

from pymodbus.server import StartAsyncSerialServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusDeviceContext, ModbusServerContext
from pymodbus import ModbusDeviceIdentification


from config import load_config
from dtsu666_constants import REGISTERS

CONFIG_FILE = "config.json"

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger("dtsu666-emulator")


class Dtsu666Emulator:
    def __init__(self, port: str, slave_id: int = 1, baudrate: int = 9600):
        self.port = port
        self.slave_id = slave_id
        self.baudrate = baudrate

        # Prepare register space (same size as before)
        self.block = ModbusSequentialDataBlock(0, [0] * 0x4052)
        self.store = ModbusDeviceContext(hr=self.block)
        self.context = ModbusServerContext(devices={self.slave_id: self.store}, single=False)

        # identity
        self.identity = ModbusDeviceIdentification()
        self.identity.VendorName = "DTSU666 Emulator"
        self.identity.ProductCode = "DTSU"
        self.identity.VendorUrl = "https://github.com/riptideio/pymodbus"
        self.identity.ProductName = "DTSU666 Energy Meter Emulator"
        #self.identity.MajorMinorRevision = ModbusVersion.short()

        # Initialize header (optional) - if you want the header at address 0
        # example header list from your code; last element will be set to slave id
        header = [207, 701, 0, 0, 0, 0, 1, 10, 0, 0, 0, 1, 167, 0, 0,
                  1000, 0, 0, 1000, 0, 0, 1000, 0, 0, 1000, 1, 10, 0, 0, 0,
                  1000, 0, 0, 1000, 0, 0, 1000, 0, 0, 1000, 0, 0, 0, 0, 3, 3, 4]
        header[-1] = self.slave_id
        self._set_values(0, header)

    def _set_values(self, address: int, registers):
        """Write list of 16-bit registers into the sequential block."""
        # ModbusSequentialDataBlock.setValues expects address (starting index) and list
        # Address here is the register index (0-based).
        self.block.setValues(address, registers)

    def set_datetime(self):
        """Write current time into registers starting at 0x002F (as 6 x 16-bit ints)."""
        now = datetime.datetime.now()
        regs = [
            int(now.second),
            int(now.minute),
            int(now.hour),
            int(now.day),
            int(now.month),
            int(now.year),
        ]
        # write to 0x002F
        self._set_values(0x002F, regs)

    def _float_to_registers(self, value: float, byteorder='>'):
        """Convert float to two 16-bit registers. byteorder '>' = big-endian."""
        # pack float to 4 bytes big-endian
        packed = struct.pack(f"{byteorder}f", float(value))
        # unpack into two unsigned shorts
        high, low = struct.unpack(f"{byteorder}HH", packed)
        return [high, low]

    def update_values(self, data: dict):
        """Update measurement registers according to REGISTERS mapping.
        REGISTERS[key] must contain 'address' and 'factor' (and optionally func/words).
        Stored register format matches what the real meter expects (32-bit float split into two registers).
        """
        for key, value in data.items():
            if key not in REGISTERS:
                logger.debug("Unknown key %s, skipping", key)
                continue
            try:
                info = REGISTERS[key]
                addr = info["address"]
                factor = info.get("factor", 1.0)
                # scale back to raw register representation: meter stores value / factor
                raw = float(value) / factor
                regs = self._float_to_registers(raw, byteorder='>')
                self._set_values(addr, regs)
                logger.debug("Wrote %s -> addr %s regs=%s (raw=%s)", key, hex(addr), regs, raw)
            except Exception as e:
                logger.warning("Failed to write %s: %s", key, e)

    async def _datetime_updater(self):
        while True:
            self.set_datetime()
            await asyncio.sleep(1)

    async def start(self):
        logger.info("Starting DTSU666 emulator on %s (slave %d)", self.port, self.slave_id)
        # Run serial server + datetime updater concurrently
        await asyncio.gather(
            StartAsyncSerialServer(
                context=self.context,
                identity=self.identity,
                port=self.port,
                framer="rtu",
                baudrate=self.baudrate,
                stopbits=1,
                bytesize=8,
                parity="N",
            ),
            self._datetime_updater(),
        )


async def main():
    cfg = load_config()
    emu_cfg = cfg["emulator"]
    logging.basicConfig(level=cfg["logging"]["level"])
    emu = Dtsu666Emulator(
        port=emu_cfg["port"],
        slave_id=cfg["device"]["id"],
        baudrate=emu_cfg.get("baudrate", 9600),
    )

    # test data (example)
    test_data = {
        "Voltage_Phase_AB": 403.6,
        "Voltage_Phase_BC": 408.0,
        "Voltage_Phase_CA": 404.5,
        "Voltage_Phase_A": 231.0,
        "Voltage_Phase_B": 235.1,
        "Voltage_Phase_C": 236.1,
        "Current_Phase_A": 0.339,
        "Current_Phase_B": 0.360,
        "Current_Phase_C": 0.352,
        "Active_Power_Phase_A": 2.8,
        "Active_Power_Phase_B": 11.8,
        "Active_Power_Phase_C": 8.5,
        "Reactive_Power_Phase_A": -76.7,
        "Reactive_Power_Phase_B": -80.0,
        "Reactive_Power_Phase_C": -79.7,
        "Power_Factor_Phase_A": 0.036,
        "Power_Factor_Phase_B": 0.140,
        "Power_Factor_Phase_C": 0.102,
        "Total_Active_Power": 23.2,
        "Total_Reactive_Power": -236.5,
        "Total_Power_Factor": 0.094,
    }

    async def updater():
        while True:
            emu.update_values(test_data)
            await asyncio.sleep(1.1)  # respect meter timing >1s between instructions

    await asyncio.gather(emu.start(), updater())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Emulator stopped.")