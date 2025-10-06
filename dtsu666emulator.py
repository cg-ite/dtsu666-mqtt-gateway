#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
import datetime
import logging
from threading import Thread

from config import load_config
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.version import version as ModbusVersion
from pymodbus.constants import Endian

from pymodbus.server.async_io import StartSerialServer
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

from dtsu666_constants import REGISTERS

CONFIG_FILE = "config.json"

WORD_ORDER = Endian.Big
BYTE_ORDER = Endian.Big

header = [207, 701, 0, 0, 0, 0, 1, 10, 0, 0, 0, 1, 167, 0, 0,
          1000, 0, 0, 1000, 0, 0, 1000, 0, 0, 1000, 1, 10, 0, 0, 0,
          1000, 0, 0, 1000, 0, 0, 1000, 0, 0, 1000, 0, 0, 0, 0, 3, 3, 4]


class Dtsu666Emulator:
    def __init__(self, device, slave_id=0x04):
        self.threads = {}
        i1 = ModbusDeviceIdentification()
        i1.VendorName = 'Pymodbus'
        i1.ProductCode = 'PM'
        i1.VendorUrl = 'http://github.com/riptideio/pymodbus/'
        i1.ProductName = 'Pymodbus Server'
        i1.ModelName = 'Pymodbus Server'
        i1.MajorMinorRevision = ModbusVersion.short()

        self.RS485Settings = {
            'port': device,
            'baudrate': 9600,
            'timeout': 1.0,  # response timeout = 1 sec
            'stopbits': 1,
            'bytesize': 8,
            'parity': 'N',
            'identity': i1
        }

        self.block = ModbusSequentialDataBlock(0, [0] * 0x4052)
        # SlaveID ins letzte Feld vom header schreiben
        header[-1] = slave_id
        self._setval(0, header)

        self.store = ModbusSlaveContext(hr=self.block)
        self.context = ModbusServerContext(slaves={slave_id: self.store}, single=False)

    def _setval(self, addr, data):
        self.block.setValues((addr), data)

    def _startserver(self):
        logging.info("Starting Modbus server with timings...")
        StartSerialServer(context=self.context, framer=ModbusRtuFramer,
                          **self.RS485Settings)

    def _datejob(self):
        while True:
            self.set_date()
            time.sleep(1)  # 1 Sekunde Updateintervall

    def startserver(self):
        self.threads['srv'] = Thread(target=self._startserver)
        self.threads['srv'].start()
        self.threads['date'] = Thread(target=self._datejob)
        self.threads['date'].start()

    def set_date(self):
        now = datetime.datetime.now()
        builder = BinaryPayloadBuilder(byteorder=BYTE_ORDER, wordorder=WORD_ORDER)
        builder.add_16bit_int(now.second)
        builder.add_16bit_int(now.minute)
        builder.add_16bit_int(now.hour)
        builder.add_16bit_int(now.day)
        builder.add_16bit_int(now.month)
        builder.add_16bit_int(now.year)
        self._setval(0x002f, builder.to_registers())

    def update(self, data):
        logging.debug(f"Send data: {data}")
        for k, v in data.items():
            reg = REGISTERS[k]["address"]
            d = v / REGISTERS[k]["factor"]
            builder = BinaryPayloadBuilder(byteorder=BYTE_ORDER, wordorder=WORD_ORDER)
            builder.add_32bit_float(d)
            self._setval(reg, builder.to_registers())
            # print(f"[Update] Register {hex(reg)} ({k}) = {v}")


if __name__ == "__main__":

    config = load_config(CONFIG_FILE)
    logging.basicConfig(level=logging.basicConfig(level=config['logging']['level']))

    em1 = Dtsu666Emulator(device=config["emulator"]["port"],
                          slave_id=config["emulator"]["slave_id"])
    em1.startserver()

    Testdata = {
        'Volts_AB': 403.6, 'Volts_BC': 408.0, 'Volts_CA': 404.5,
        'Volts_L1': 231.0, 'Volts_L2': 235.1, 'Volts_L3': 236.1,
        'Current_L1': 0.339, 'Current_L2': 0.36, 'Current_L3': 0.352,
        'Active_Power_L1': 2.8, 'Active_Power_L2': 11.8, 'Active_Power_L3': 8.5,
        'Reactive_Power_L1': -76.7, 'Reactive_Power_L2': -80.0, 'Reactive_Power_L3': -79.7,
        'Power_Factor_L1': 0.036, 'Power_Factor_L2': 0.14, 'Power_Factor_L3': 0.102,
        'Total_System_Active_Power': 23.2, 'Total_System_Reactive_Power': -236.5,
        'Total_System_Power_Factor': 0.094,
    }

    while True:
        em1.update(Testdata)
        time.sleep(1.1)  # min. 1s Abstand zwischen zwei Befehlen
