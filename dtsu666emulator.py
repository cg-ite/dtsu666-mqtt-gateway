#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import datetime
import logging
import signal
import struct

from pymodbus.server import ModbusSerialServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusDeviceContext, ModbusServerContext
from pymodbus import ModbusDeviceIdentification, FramerType

from config import load_config
from dtsu666_constants import *

CONFIG_FILE = "config.json"

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger("dtsu666-emulator")


class Dtsu666Emulator:
    """Emulator class for Chint DTSU666 energy meter"""

    def __init__(self, datablock:ModbusSequentialDataBlock,
                 port: str, device_id: int = 1, baudrate: int = 9600):
        self.datetime_task = None
        self.port = port
        self.device_id = device_id
        self.baudrate = baudrate

        self.server_task = None
        self.stop_event = asyncio.Event()

        # Prepare register space
        self.block = datablock
        self.store = ModbusDeviceContext(hr=self.block)
        self.context = ModbusServerContext(devices={self.device_id: self.store}, single=False)

        # identity
        self.identity = ModbusDeviceIdentification()
        self.identity.VendorName = "DTSU666 Emulator"
        self.identity.ProductCode = "DTSU"
        self.identity.VendorUrl = "https://github.com/riptideio/pymodbus"
        self.identity.ProductName = "DTSU666 Energy Meter Emulator"

        self.server = ModbusSerialServer(
            context=self.context,
            identity=self.identity,
            port=self.port,
            framer=FramerType.RTU,
            baudrate=self.baudrate,
            stopbits=1,
            bytesize=8,
            parity="N",
        )

        # header
        header = [207, 701, 0, 0, 0, 0, 1, 10, 0, 0, 0, 1, 167, 0, 0,
                  1000, 0, 0, 1000, 0, 0, 1000, 0, 0, 1000, 1, 10, 0, 0, 0,
                  1000, 0, 0, 1000, 0, 0, 1000, 0, 0, 1000, 0, 0, 0, 0, 3, 3, 4]

        header[-1] = self.device_id
        self._set_values(0, header)

    # --------------------------
    # Register setter helpers
    # --------------------------

    def _set_values(self, address: int, registers):
        self.block.setValues(address, registers)

    def set_datetime(self):
        now = datetime.datetime.now()
        regs = [now.second, now.minute, now.hour,
                now.day, now.month, now.year]
        self._set_values(0x002F, regs)

    def _float_to_registers(self, value: float, byteorder='>'):
        packed = struct.pack(f"{byteorder}f", float(value))
        high, low = struct.unpack(f"{byteorder}HH", packed)
        return [high, low]

    def update_values(self, data: dict):
        for key, value in data.items():
            if key not in REGISTERS:
                continue
            info = REGISTERS[key]
            addr = info["address"]
            factor = info.get("factor", 1.0)
            raw = float(value) / factor
            regs = self._float_to_registers(raw)
            self._set_values(addr, regs)

    # --------------------------
    # Background tasks
    # --------------------------

    async def _datetime_updater(self):
        while not self.stop_event.is_set():
            self.set_datetime()
            await asyncio.sleep(1)

    # --------------------------
    # Start / Stop
    # --------------------------

    async def start(self):
        logger.info("Starting DTSU666 emulator on %s (slave %d)", self.port, self.device_id)

        # Server starten (AsyncIO Start)
        async def run_server():
            await self.server.serve_forever()  # blockiert bis stop()

        self.server_task = asyncio.create_task(run_server())

        # Paralleler Task
        self.datetime_task = asyncio.create_task(self._datetime_updater())

        logger.info("DTSU666 emulator started.")

    async def stop(self):
        logger.info("Stopping DTSU666 emulator...")

        # stop background loops
        self.stop_event.set()

        # stop server cleanly
        if self.server:
            await self.server.shutdown()

        # cancel running tasks
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass

        if hasattr(self, "datetime_task"):
            self.datetime_task.cancel()

        logger.info("DTSU666 emulator stopped.")


async def main():
    cfg = load_config()
    emu_cfg = cfg["emulator"]
    logging.basicConfig(level=cfg["logging"]["level"])
    emu = Dtsu666Emulator(
        port=emu_cfg["port"],
        device_id=cfg["device"]["id"],
        baudrate=emu_cfg.get("baudrate", 9600),
    )

    # test data (example)
    test_data = {
        VOLTAGE_PHASE_AB: 403.6,
        VOLTAGE_PHASE_BC: 408.0,
        VOLTAGE_PHASE_CA: 404.5,

        VOLTAGE_PHASE_A: 231.0,
        VOLTAGE_PHASE_B: 235.1,
        VOLTAGE_PHASE_C: 236.1,

        CURRENT_PHASE_A: 0.339,
        CURRENT_PHASE_B: 0.360,
        CURRENT_PHASE_C: 0.352,

        ACTIVE_POWER_PHASE_A: 2.8,
        ACTIVE_POWER_PHASE_B: 11.8,
        ACTIVE_POWER_PHASE_C: 3.5,

        REACTIVE_POWER_PHASE_A: -76.7,
        REACTIVE_POWER_PHASE_B: -80.0,
        REACTIVE_POWER_PHASE_C: -79.7,

        POWER_FACTOR_PHASE_A: 0.036,
        POWER_FACTOR_PHASE_B: 0.140,
        POWER_FACTOR_PHASE_C: 0.102,

        TOTAL_ACTIVE_POWER: 23.2,
        TOTAL_REACTIVE_POWER: -27.5,
        TOTAL_POWER_FACTOR: 0.094,
    }

    # Hintergrund-Task: alle 1.1 s neue Werte schreiben
    async def updater():
        while not emu.stop_event.is_set():
            emu.update_values(test_data)
            await asyncio.sleep(1.1)

    # -----------------------------
    # Start des Emulators
    # -----------------------------
    await emu.start()
    updater_task = asyncio.create_task(updater())

    # -----------------------------
    # Shutdown-Handler (SIGINT/SIGTERM)
    # -----------------------------
    stop_event = asyncio.Event()

    def shutdown_handler(*args):
        logging.info("Shutdown signal received...")
        stop_event.set()

    # Signalhandler registrieren
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, shutdown_handler)
    loop.add_signal_handler(signal.SIGTERM, shutdown_handler)

    # Warten, bis Stopp-Signal kommt
    await stop_event.wait()

    # Server stoppen
    logging.info("Stopping emulator...")
    updater_task.cancel()
    await emu.stop()

    logging.info("Shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Emulator stopped.")
