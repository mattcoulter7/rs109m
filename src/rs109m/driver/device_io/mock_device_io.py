from .base import DeviceIO
from ..config import RS109mConfig

class MockDeviceIO(DeviceIO):
    """
    A self-contained mock that simulates an RS-109M device with an internal RS109mConfig.
    
    - On handshake (0x59,0x01,0x42,...), returns b'\x95\x20' for success.
    - On read cmd [0x51, length], returns [0x25, length] + the internal device_config bytes.
    - On write cmd [0x55, length], the next write call is assumed to be the new config data
      which overwrites the internal device_config, then returns [0x75, length].
      
    This allows you to do multiple load_config(...) + write_config(...) operations in
    the same test, and any newly written configuration is “remembered” by the mock device.
    """

    def __init__(self, extended: bool = False):
        self.extended = extended
        self.device_config = RS109mConfig()  # Our "on-device" config
        self.write_buffer = bytearray()
        self.read_cursor = 0
        self.read_buffer = bytearray()

        # State tracking for partial operations
        self._state = "IDLE"
        self._expect_write_len = 0

    def write(self, data) -> None:
        """Intercept commands/data and build the appropriate responses in read_buffer."""
        # Convert list->bytes if needed
        if isinstance(data, list):
            data = bytes(data)

        # Keep track of everything we send (for debugging/inspection).
        self.write_buffer += data

        # If we’re currently receiving config bytes for a write:
        if self._state == "WRITING_CONFIG":
            if len(data) == self._expect_write_len:
                # Overwrite our device_config with the new bytes
                config_len = min(self._expect_write_len, len(self.device_config.config))
                new_config = bytearray(data[:config_len])
                # Insert into device_config at the front
                existing = self.device_config.config
                self.device_config.config = new_config + existing[config_len:]
                
                # Now respond with write ACK
                self.read_buffer += bytes([0x75, self._expect_write_len])
                self._state = "IDLE"
            else:
                # For simplicity, assume the entire config arrives in one chunk
                pass
            return

        # Otherwise parse commands:
        if len(data) >= 3 and data[0] == 0x59 and data[1] == 0x01 and data[2] == 0x42:
            # Password handshake => respond success
            self.read_buffer += b"\x95\x20"

        elif len(data) == 2 and data[0] == 0x51:
            # read command: data = [0x51, length]
            length = data[1]
            self._respond_with_read(length)

        elif len(data) == 2 and data[0] == 0x55:
            # write command: data = [0x55, length]
            self._state = "WRITING_CONFIG"
            self._expect_write_len = data[1]

        else:
            # Possibly the driver is sending password bytes or partial config bytes
            # in separate writes. For simplicity, we do nothing else here.
            pass

    def read(self, num_bytes: int) -> bytes:
        """Pull from read_buffer starting at read_cursor; pad with zero if short."""
        data = self.read_buffer[self.read_cursor : self.read_cursor + num_bytes]
        self.read_cursor += num_bytes
        return data.ljust(num_bytes, b'\x00')

    def reset(self) -> None:
        """
        Called by RS109mDriver after an operation.
        We just reset the read cursor, so the driver can re-read if it wants,
        or we can build new data in read_buffer for the next command.
        """
        self.read_buffer.clear()
        self.read_cursor = 0
        self._state = "IDLE"

    def get_written_data(self) -> bytes:
        """For debugging: the entire sequence that was written to the mock device."""
        return bytes(self.write_buffer)

    def _respond_with_read(self, length: int):
        """
        Helper to build the read ack plus the current device_config bytes.
        """
        # Acknowledge: 0x25, length
        self.read_buffer += bytes([0x25, length])

        # Return the relevant portion of our device_config
        config_bytes = self.device_config.config
        read_size = min(len(config_bytes), length)
        self.read_buffer += config_bytes[:read_size]

        # If length is bigger than actual config, fill with dummy to match length
        if read_size < length:
            self.read_buffer += b"\xAA" * (length - read_size)
