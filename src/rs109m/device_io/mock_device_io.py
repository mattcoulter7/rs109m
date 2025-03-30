from .base import DeviceIO


class MockDeviceIO(DeviceIO):
    def __init__(self):
        self.buffer = bytearray()
        self.expected_read_data = bytearray()
        self._original_read_data = bytearray()

        # Setup initial expected read data (can be overridden for tests)
        self.set_expected_read(self.get_initial_read_data())

    def write(self, data) -> None:
        if isinstance(data, list):
            data = bytes(data)
        self.buffer.extend(data)

    def read(self, num_bytes: int) -> bytes:
        result = self.expected_read_data[:num_bytes]
        self.expected_read_data = self.expected_read_data[num_bytes:]
        return result.ljust(num_bytes, b'\x00')

    def set_expected_read(self, data: bytes) -> None:
        self._original_read_data = bytearray(data)
        self.expected_read_data = bytearray(data)

    def reset(self) -> None:
        self.expected_read_data = bytearray(self._original_read_data)

    def get_initial_read_data(self) -> bytes:
        # Default to empty; test code will override this
        return b""
