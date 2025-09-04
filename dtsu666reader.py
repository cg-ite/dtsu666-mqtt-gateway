#!/usr/bin/env python3
import argparse
import minimalmodbus
from config import load_config

from dtsu666_constants import FOUR_WIRE_KEYS, MEASUREMENTS

CONFIG_FILE = "config.json"


class Dtsu666Reader:
    """Reader class for Chint DTSU666 energy meter"""

    def __init__(self, port: str, baudrate: int, slave_id: int):
        self.port = port
        self.baudrate = baudrate
        self.slave_id = slave_id

        self.instrument = minimalmodbus.Instrument(self.port, self.slave_id)
        self.instrument.serial.baudrate = self.baudrate
        self.instrument.serial.bytesize = 8
        self.instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
        self.instrument.serial.stopbits = 1
        self.instrument.serial.timeout = 1
        self.instrument.mode = minimalmodbus.MODE_RTU

    def read_values(self):
        """Reads the most important values from the DTSU666"""
        data = {}
        for key in FOUR_WIRE_KEYS:
            try:
                spec = MEASUREMENTS[key]
                raw = self.instrument.read_float(spec["address"], spec["func"], spec["words"])
                data[key] = raw * spec["factor"]
            except Exception as e:
                print(f"Fehler beim Lesen von {key}: {e}")
                data[key] = None
        return data

def main():
    """Reads the consumption data of a dtsu666 once"""

    # load defaults from config.json
    config = load_config(CONFIG_FILE)["dtsu666"]

    parser = argparse.ArgumentParser(
        description=(
            "Chint DTSU666 Modbus Reader: "
            "A command line tool for testing the Modbus connection "
            "to a DTSU666 energy meter"
        )
    )
    parser.add_argument("--port", help="Serial port (e.g. /dev/ttyUSB0)")
    parser.add_argument("--baudrate", type=int, help="Baudrate (default: 9600)")
    parser.add_argument("--slaveId", type=int, help="Modbus Slave ID (default: 1)")
    args = parser.parse_args()

    # override config with CLI arguments
    if args.port:
        config["port"] = args.port
    if args.baudrate:
        config["baudrate"] = args.baudrate
    if args.slaveId:
        config["slaveId"] = args.slaveId

    reader = Dtsu666Reader(
        port=config["port"], baudrate=config["baudrate"], slave_id=config["slaveId"]
    )

    values = reader.read_values()
    if values:
        for k, v in values.items():
            print(f"{k:30}: {v:.3f}")


if __name__ == "__main__":
    main()
