import serial
from rs109m.constants import BAUDRATE

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
            timeout=1,
            write_timeout=3,
        )
        self.ser.open()
        # Flush any leftover data to stabilize the connection
        self.ser.read(0xffff)
        self.ser.timeout = 3

    def write(self, data) -> None:
        # Accept either a list of integers or a bytes-like object.
        if isinstance(data, list):
            data = bytes(data)
        self.ser.write(data)

    def read(self, num_bytes: int) -> bytes:
        return self.ser.read(num_bytes)

    def reset(self) -> None:
        self.ser.reset_input_buffer()
