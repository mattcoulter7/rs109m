from pydantic import BaseModel, Field, field_validator
from typing import Optional

from .ship_type import ShipType


class RS109mConfig(BaseModel):
    mmsi: Optional[int] = Field(
        None, ge=100000000, le=999999999, description="MMSI (9-digit)"
    )
    name: Optional[str] = Field(None, max_length=50, description="Ship name")
    interval: Optional[int] = Field(
        None, ge=30, le=600, description="Transmit interval in seconds [30..600]"
    )
    ship_type: Optional[ShipType] = Field(None, description="Ship type")
    callsign: Optional[str] = Field(None, max_length=6, description="Call sign (max 6 characters)")
    vendorid: Optional[str] = Field(None, max_length=3, description="AIS unit vendor id (3 characters)")
    unitmodel: Optional[int] = Field(None, ge=0, le=15, description="AIS unit vendor model code (0-15)")
    sernum: Optional[int] = Field(None, ge=0, le=1048575, description="AIS unit serial number (0-1048575)")
    refa: Optional[int] = Field(None, ge=0, le=511, description="Reference A (0-511)")
    refb: Optional[int] = Field(None, ge=0, le=511, description="Reference B (0-511)")
    refc: Optional[int] = Field(None, ge=0, le=63, description="Reference C (0-63)")
    refd: Optional[int] = Field(None, ge=0, le=63, description="Reference D (0-63)")

    @field_validator("callsign")
    @classmethod
    def validate_callsign(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 6:
            raise ValueError("Callsign must be at most 6 characters long")
        return v

    def get_config_str(self) -> str:
        """
        Returns a string representation of the configuration.
        """
        out = []
        out.append(f"  MMSI: {self.mmsi}")
        out.append(f"  Name: {self.name}")
        out.append(f"  TX interval (s): {self.interval}")
        out.append(f"  Ship type: {self.ship_type}")
        out.append(f"  Callsign: {self.callsign}")
        out.append(f"  VendorID: {self.vendorid}")
        out.append(f"  UnitModel: {self.unitmodel}")
        out.append(f"  UnitSerial: {self.sernum}")
        out.append(f"  Reference point A (m): {self.refa} (read-only battery voltage {self.refa/10.0:.1f}V)")
        out.append(f"  Reference point B (m): {self.refb}")
        out.append(f"  Reference point C (m): {self.refc}")
        out.append(f"  Reference point D (m): {self.refd}")

        return "\n".join(out)


class DeviceConnectionMixIn(BaseModel):
    device: str = Field(..., description="Serial port (e.g. /dev/ttyUSB0)"),
    mock: bool = Field(False, description="Use the mock device IO instead of a real device"),
    password: Optional[str] = Field(None, pattern=r"^[0-9]{0,6}$", description="Password (0 to 6 digits)")
    extended: bool = Field(False, description="Operate on extended config size")


class RS109mReadConfigRequest(DeviceConnectionMixIn):
    """
    A request object for reading the configuration.
    (Add fields if needed; otherwise, leave empty.)
    """
    # No additional fields needed for now.
    ...

class RS109mWriteConfigRequest(DeviceConnectionMixIn):
    """
    A request object for writing a new configuration.
    """
    config: RS109mConfig
