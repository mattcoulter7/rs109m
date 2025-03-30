import re
import logging

from .device_io.base import DeviceIO
from .constants import DEFAULT_PASSWORD, PASSWORD_MAXLEN
from .config import RS109mConfig

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

    def load_config(
        self,
        config: RS109mConfig,
        extended: bool,
        password: str,
        noread: bool,
    ) -> None:
        """
        Handles the handshake with the device and loads configuration data
        into the provided config object.
        """
        num_bytes = config.default_len
        if extended:
            num_bytes = 0xff

        # Perform the password handshake
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

        if not noread:
            self.device_io.write([0x51, num_bytes])
            r = self.device_io.read(2)
            if r != bytes([0x25, num_bytes]):
                raise Exception("Could not read config header, got: " + r.hex(' '))
            data = self.device_io.read(num_bytes)
            if len(data) != num_bytes:
                raise Exception("Incomplete config data.")
            config.config = data

        self.device_io.reset()

    def write_config(
        self,
        config: RS109mConfig,
        extended: bool,
    ) -> None:
        """
        Writes the current configuration to the device.
        """
        num_bytes = config.default_len
        if extended:
            num_bytes = 0xff

        self.device_io.write([0x55, num_bytes])
        self.device_io.write(config.config[:num_bytes])
        r = self.device_io.read(2)
        if r != bytes([0x75, num_bytes]):
            raise Exception("Write failed.")
        logger.info("Config written successfully!")

        self.device_io.reset()

    def read_config(
        self,
        extended: bool,
        password: str,
        noread: bool,
    ):
        config = RS109mConfig()

        self.load_config(
            config=config,
            extended=extended,
            password=password,
            noread=noread,
        )

        return config
