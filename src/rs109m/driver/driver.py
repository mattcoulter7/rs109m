import re
import logging

from contextlib import contextmanager

from .device_io.base import DeviceIO
from .constants import DEFAULT_PASSWORD, PASSWORD_MAXLEN
from .config import RS109mRawConfig

logger = logging.getLogger(__name__)


class RS109mDriver:
    def __init__(
        self,
        device_io: DeviceIO,
    ):
        """
        device_io: an instance of DeviceIO (e.g. SerialDeviceIO or MockDeviceIO).
                   Can be None if no device is supplied.
        """
        self.device_io = device_io
        self.handshook = False

    @contextmanager
    def handshake(
        self,
        password: str,
    ):
        if self.handshook:
            yield
            return

        """
        Context manager to perform and validate handshake.
        After exiting, it calls device_io.reset().
        """
        if password is not None:
            if not re.match(f"^[0-9]{{0,{PASSWORD_MAXLEN}}}$", password):
                raise ValueError(f"Password incorrect: should match [0-9]{{0,{PASSWORD_MAXLEN}}}")
            password_prepared = (password.encode() + DEFAULT_PASSWORD.encode())[:PASSWORD_MAXLEN]
            self.device_io.write([0x59, 0x01, 0x42, PASSWORD_MAXLEN])
            self.device_io.write(password_prepared)
        else:
            self.device_io.write([0x59, 0x01, 0x42, 0x00])

        r = self.device_io.read(2)
        if r != b'\x95\x20':
            raise Exception("Could not initialize with password.")

        try:
            self.handshook = True
            yield
        finally:
            self.device_io.reset()

    def read_config(
        self,
        *,
        password: str,
        extended: bool = False,
    ) -> RS109mRawConfig:
        """
        Handles the handshake with the device and loads configuration data
        into the provided config object.
        """
        config = RS109mRawConfig()

        num_bytes = config.default_len
        if extended:
            num_bytes = 0xff

        with self.handshake(password):
            self.device_io.write([0x51, num_bytes])
            r = self.device_io.read(2)
            if r != bytes([0x25, num_bytes]):
                raise Exception("Could not read config header, got: " + r.hex(' '))
            data = self.device_io.read(num_bytes)
            if len(data) != num_bytes:
                raise Exception("Incomplete config data.")
            config.config = data

        return config

    def write_config(
        self,
        config: RS109mRawConfig,
        *,
        password: str,
        extended: bool = False,
    ) -> None:
        """
        Writes the current configuration to the device.
        """
        num_bytes = config.default_len
        if extended:
            num_bytes = 0xff

        with self.handshake(password):
            self.device_io.write([0x55, num_bytes])
            self.device_io.write(config.config[:num_bytes])
            r = self.device_io.read(2)
            if r != bytes([0x75, num_bytes]):
                raise Exception("Write failed.")
            logger.info("Config written successfully!")

        return None
