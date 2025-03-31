import serial
from typing import override

from rs109m.driver.constants import BAUDRATE, SERIAL_TIMEOUT, SERIAL_WRITE_TIMEOUT

from .base import DeviceIO


class SerialDeviceIO(DeviceIO):
    def __init__(self, port: str):
        # Set up the serial device with the desired configuration
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = BAUDRATE
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.timeout = SERIAL_TIMEOUT
        self.ser.write_timeout = SERIAL_WRITE_TIMEOUT

        self.ser.open()

        # Flush any leftover data to stabilize the connection
        self.ser.read(0xffff)

    @override
    def write(self, data) -> None:
        # Accept either a list of integers or a bytes-like object.
        if isinstance(data, list):
            data = bytes(data)
        self.ser.write(data)

    @override
    def read(self, num_bytes: int) -> bytes:
        return self.ser.read(num_bytes)

    @override
    def reset(self) -> None:
        self.ser.reset_input_buffer()
