#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import signal
from pymodbus.client import AsyncModbusSerialClient

from datablocks import LoggingDataBlock
from dtsu666reader import Dtsu666Reader
from dtsu666emulator import Dtsu666Emulator   # <-- Deine Emulator-Klasse importieren
from config import load_config
from dtsu666_constants import REGISTERS


# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
logging.basicConfig(
    filename="reader.txt",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("dtsu-reader")

async def main():
    cfg = load_config()
    emu_cfg = cfg["emulator"]

    emulator = Dtsu666Emulator(
        datablock= LoggingDataBlock(),
        port=emu_cfg["port"],
        device_id=cfg["device"]["id"],
        baudrate=emu_cfg.get("baudrate", 9600),
    )

    # Start Emulator
    await emulator.start()

    # Signal handling
    stop_event = asyncio.Event()

    def shutdown_handler(*args):
        logger.info("Shutdown signal received...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, shutdown_handler)
