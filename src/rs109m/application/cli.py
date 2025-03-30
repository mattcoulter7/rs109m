import typer
import serial
import re
import logging

from typing import Optional

from rs109m.config import RS109mConfig
from rs109m.constants import DEFAULT_PASSWORD, BAUDRATE, PASSWORD_MAXLEN

logger = logging.getLogger(__name__)
app = typer.Typer()


@app.command()
def main(
    device: Optional[str] = typer.Option(
        ...,
        "--device",
        "-d",
        help="Serial port device (e.g. /dev/ttyUSB0)",
        prompt="Enter serial port device (e.g. /dev/ttyUSB0)"
    ),
    mmsi: Optional[int] = typer.Option(
        None,
        "--mmsi",
        "-m",
        help="MMSI (leave blank to keep current configuration)",
        prompt="Enter MMSI (leave blank to keep current configuration)"
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Ship name (leave blank to keep current configuration)",
        prompt="Enter ship name (leave blank to keep current configuration)"
    ),
    interval: Optional[int] = typer.Option(
        None,
        "--interval",
        "-i",
        help="Transmit interval in seconds [30..600] (leave blank to keep current configuration)",
        prompt="Enter transmit interval in seconds [30..600] (leave blank to keep current configuration)"
    ),
    ship_type: Optional[int] = typer.Option(
        None,
        "--type",
        "-t",
        help="Ship type (e.g. sail=36, pleasure craft=37) (leave blank to keep current configuration)",
        prompt="Enter ship type (e.g. sail=36, pleasure craft=37) (leave blank to keep current configuration)"
    ),
    callsign: Optional[str] = typer.Option(
        None,
        "--callsign",
        "-c",
        help="Call sign (leave blank to keep current configuration)",
        prompt="Enter call sign (leave blank to keep current configuration)"
    ),
    vendorid: Optional[str] = typer.Option(
        None,
        "--vendorid",
        "-v",
        help="AIS unit vendor id (3 characters) (leave blank to keep current configuration)",
        prompt="Enter AIS unit vendor id (3 characters) (leave blank to keep current configuration)"
    ),
    unitmodel: Optional[int] = typer.Option(
        None,
        "--unitmodel",
        "-u",
        help="AIS unit vendor model code (leave blank to keep current configuration)",
        prompt="Enter AIS unit vendor model code (leave blank to keep current configuration)"
    ),
    sernum: Optional[int] = typer.Option(
        None,
        "--sernum",
        "-s",
        help="AIS unit serial num (leave blank to keep current configuration)",
        prompt="Enter AIS unit serial num (leave blank to keep current configuration)"
    ),
    refa: Optional[int] = typer.Option(
        None,
        "--refa",
        "-A",
        help="Reference A (distance AIS to bow in m; Net Locator sends battery voltage instead) (leave blank to keep current configuration)",
        prompt="Enter Reference A (distance AIS to bow in m; Net Locator sends battery voltage instead) (leave blank to keep current configuration)"
    ),
    refb: Optional[int] = typer.Option(
        None,
        "--refb",
        "-B",
        help="Reference B (distance AIS to stern in m) (leave blank to keep current configuration)",
        prompt="Enter Reference B (distance AIS to stern in m) (leave blank to keep current configuration)"
    ),
    refc: Optional[int] = typer.Option(
        None,
        "--refc",
        "-C",
        help="Reference C (distance AIS to port in m) (leave blank to keep current configuration)",
        prompt="Enter Reference C (distance AIS to port in m) (leave blank to keep current configuration)"
    ),
    refd: Optional[int] = typer.Option(
        None,
        "--refd",
        "-D",
        help="Reference D (distance AIS to starboard in m) (leave blank to keep current configuration)",
        prompt="Enter Reference D (distance AIS to starboard in m) (leave blank to keep current configuration)"
    ),
    password: Optional[str] = typer.Option(
        None,
        "--password",
        "-P",
        help="Password to access Net Locator (leave blank to keep current configuration)",
        prompt="Enter password to access Net Locator (leave blank to keep current configuration)"
    ),
    extended: bool = typer.Option(
        False,
        "--extended",
        "-E",
        help="Operate on 0xff size config instead of default 0x40"
    ),
    write: bool = typer.Option(
        False,
        "--write",
        "-W",
        help="Write config to Net Locator"
    ),
    noread: bool = typer.Option(
        False,
        "--noread",
        "-R",
        help="Do not read from Net Locator"
    )
):
    # Initialize configuration
    c = RS109mConfig()
    num_bytes = c.default_len
    if extended:
        num_bytes = 0xff

    ser = None
    if device is not None:
        ser = serial.Serial()
        ser.port = device
        ser.baudrate = BAUDRATE
        ser.bytesize = serial.EIGHTBITS
        ser.parity = serial.PARITY_NONE
        ser.stopbits = serial.STOPBITS_ONE

        ser.timeout = 1
        ser.write_timeout = 3

        ser.open()

        # Try a read to establish a more reliable connection then update timeout
        ser.read(0xffff)
        ser.timeout = 3

        if password is not None:
            # Validate password: should be digits and up to PASSWORD_MAXLEN in length.
            if not re.match("^[0-9]{0," + str(PASSWORD_MAXLEN) + "}$", password):
                logger.error("Password: incorrect format, should match [0-9]{0," + str(PASSWORD_MAXLEN) + "}")
                raise typer.Exit(code=1)

            password_prepared = (password.encode() + DEFAULT_PASSWORD.encode())[:PASSWORD_MAXLEN]
            ser.write([0x59, 0x01, 0x42, PASSWORD_MAXLEN])
            ser.write(password_prepared)
        else:
            # This seems to work even with a password set
            ser.write([0x59, 0x01, 0x42, 0x00])

        r = ser.read(2)
        if r != b'\x95\x20':
            logger.error("Could not initialize with password.")
            raise typer.Exit(code=1)

        if not noread:
            ser.write([0x51, num_bytes])
            r = ser.read(2)
            if r != bytes([0x25, num_bytes]):
                logger.error("Could not read config, got this instead:")
                logger.debug(r.hex(' '))
                raise typer.Exit(code=1)

            config = ser.read(num_bytes)
            if len(config) == num_bytes:
                c.config = config
            else:
                logger.error("Could not read config from device")
                raise typer.Exit(code=1)
    else:
        logger.info("Operating on default config:")
        logger.info("")

    # Apply configuration parameters (if provided)
    if mmsi is not None:
        c.mmsi = mmsi

    if name is not None:
        c.name = name

    if interval is not None:
        c.interval = interval

    if ship_type is not None:
        c.shipncargo = ship_type

    if callsign is not None:
        c.callsign = callsign

    if vendorid is not None:
        c.vendorid = vendorid

    if unitmodel is not None:
        c.unitmodel = unitmodel

    if sernum is not None:
        c.sernum = sernum

    if refa is not None:
        c.refa = refa

    if refb is not None:
        c.refb = refb

    if refc is not None:
        c.refc = refc

    if refd is not None:
        c.refd = refd

    # Logging the config details
    logger.info("  MMSI: %s", c.mmsi)
    logger.info("  Name: %s", c.name)
    logger.info("  TX interval (s): %d", c.interval)
    logger.info("  Ship type: %s", c.shipncargo)
    logger.info("  Callsign: %s", c.callsign)
    logger.info("  VendorID: %s", c.vendorid)
    logger.info("  UnitModel: %d", c.unitmodel)
    logger.info("  UnitSerial: %d", c.sernum)
    logger.info("  Reference point A (m): %d (read-only battery voltage %.1fV)", c.refa, c.refa / 10.0)
    logger.info("  Reference point B (m): %d", c.refb)
    logger.info("  Reference point C (m): %d", c.refc)
    logger.info("  Reference point D (m): %d", c.refd)
    logger.info("")
    logger.info("[ 0x" + c.config[:num_bytes].hex('#').replace('#', ', 0x') + " ]")

    # Write config to device if requested
    if device is not None and write:
        ser.write([0x55, num_bytes])
        ser.write(c.config[:num_bytes])
        r = ser.read(2)
        if r != bytes([0x75, num_bytes]):
            logger.error("Write failed")
            raise typer.Exit(code=1)
        else:
            logger.info("Config written successfully!")
    else:
        if write:
            logger.error("Must supply serial device with -d option.")
            raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
