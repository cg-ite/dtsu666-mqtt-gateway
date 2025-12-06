import logging

from pymodbus.datastore import ModbusSequentialDataBlock

from dtsu666_constants import REGISTERS

logging.basicConfig(
    filename="reader.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("dtsu-logger")


class LoggingDataBlock(ModbusSequentialDataBlock):
    """Datablock class for debugging the communication between WR and DTSU666"""
    def __init__(self):
        super().__init__(0, [0] * 0x4000)

    def getValues(self, address, count=1):
        if address not in REGISTERS:
            logger.info("WR wants to read unknown address %s", address)
            return
        logger.info("WR reads address %s (%s) with count: %i", REGISTERS[address]["name"], address, count)
