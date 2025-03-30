from abc import ABC, abstractmethod

class DeviceIO(ABC):
    @abstractmethod
    def write(self, data) -> None:
        """Write data to the device."""
        ...

    @abstractmethod
    def read(self, num_bytes: int) -> bytes:
        """Read data from the device."""
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset the input buffer"""
        ...
