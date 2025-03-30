import serial
from typing import override

from rs109m.driver.constants import BAUDRATE, SERIAL_TIMEOUT, SERIAL_WRITE_TIMEOUT

from .base import DeviceIO


class SerialDeviceIO(DeviceIO):
    def __init__(self, port: str):
        # Set up the serial device with the desired configuration
        self.ser = serial.Serial(
            port=port,
            baudrate=BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=SERIAL_TIMEOUT,
            write_timeout=SERIAL_WRITE_TIMEOUT,
        )
        self.ser.open()

        # Flush any leftover data to stabilize the connection
        self.ser.read(0xffff)
        self.ser.timeout = SERIAL_WRITE_TIMEOUT

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
