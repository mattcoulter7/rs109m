import typer
import logging
from typing import Optional

from rs109m.config import RS109mConfig
from rs109m.constants import DEFAULT_PASSWORD
from rs109m.device_io import SerialDeviceIO, MockDeviceIO
from rs109m.device_config_io import DeviceConfigIO
from rs109m.application.validate import (
    validate_interval, validate_vendorid, validate_unitmodel, 
    validate_sernum, validate_refa, validate_refb, 
    validate_refc, validate_refd, validate_password,
    validate_callsign,
)

logger = logging.getLogger(__name__)
app = typer.Typer()


@app.command()
def main(
    device: Optional[str] = typer.Option(
        None,
        "--device",
        "-d",
        help="Serial port device (e.g. /dev/ttyUSB0) (leave blank for default config)",
        prompt="Enter serial port device (leave blank for default config)"
    ),
    mock: bool = typer.Option(
        False,
        "--mock",
        help="Use the mock device IO instead of a real device"
    ),
    mmsi: Optional[int] = typer.Option(
        ...,
        "--mmsi",
        "-m",
        help="MMSI (leave blank to keep current configuration)",
        prompt="Enter MMSI (leave blank to keep current configuration)"
    ),
    name: Optional[str] = typer.Option(
        ...,
        "--name",
        "-n",
        help="Ship name (leave blank to keep current configuration)",
        prompt="Enter ship name (leave blank to keep current configuration)"
    ),
    interval: Optional[int] = typer.Option(
        ...,
        "--interval",
        "-i",
        help="Transmit interval in seconds [30..600] (leave blank to keep current configuration)",
        prompt="Enter transmit interval in seconds (leave blank to keep current configuration)",
        callback=validate_interval
    ),
    ship_type: Optional[int] = typer.Option(
        ...,
        "--type",
        "-t",
        help="Ship type (leave blank to keep current configuration)",
        prompt="Enter ship type (leave blank to keep current configuration)"
    ),
    callsign: Optional[str] = typer.Option(
        ...,
        "--callsign",
        "-c",
        help="Call sign (max 6 characters; leave blank to keep current configuration)",
        prompt="Enter call sign (max 6 characters; leave blank to keep current configuration)",
        callback=validate_callsign
    ),
    vendorid: Optional[str] = typer.Option(
        ...,
        "--vendorid",
        "-v",
        help="AIS unit vendor id (3 characters) (leave blank to keep current configuration)",
        prompt="Enter vendor id (leave blank to keep current configuration)",
        callback=validate_vendorid
    ),
    unitmodel: Optional[int] = typer.Option(
        ...,
        "--unitmodel",
        "-u",
        help="AIS unit vendor model code (leave blank to keep current configuration)",
        prompt="Enter vendor model code (leave blank to keep current configuration)",
        callback=validate_unitmodel
    ),
    sernum: Optional[int] = typer.Option(
        ...,
        "--sernum",
        "-s",
        help="AIS unit serial num (leave blank to keep current configuration)",
        prompt="Enter serial number (leave blank to keep current configuration)",
        callback=validate_sernum
    ),
    refa: Optional[int] = typer.Option(
        ...,
        "--refa",
        "-A",
        help="Reference A (leave blank to keep current configuration)",
        prompt="Enter Reference A (leave blank to keep current configuration)",
        callback=validate_refa
    ),
    refb: Optional[int] = typer.Option(
        ...,
        "--refb",
        "-B",
        help="Reference B (leave blank to keep current configuration)",
        prompt="Enter Reference B (leave blank to keep current configuration)",
        callback=validate_refb
    ),
    refc: Optional[int] = typer.Option(
        ...,
        "--refc",
        "-C",
        help="Reference C (leave blank to keep current configuration)",
        prompt="Enter Reference C (leave blank to keep current configuration)",
        callback=validate_refc
    ),
    refd: Optional[int] = typer.Option(
        ...,
        "--refd",
        "-D",
        help="Reference D (leave blank to keep current configuration)",
        prompt="Enter Reference D (leave blank to keep current configuration)",
        callback=validate_refd
    ),
    password: Optional[str] = typer.Option(
        DEFAULT_PASSWORD,
        "--password",
        "-P",
        help="Password (leave blank to keep current configuration)",
        prompt="Enter password (leave blank to keep current configuration)",
        callback=validate_password
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
        help="Write config to device"
    ),
    noread: bool = typer.Option(
        False,
        "--noread",
        "-R",
        help="Do not read from device"
    )
):
    # Create a configuration object
    config = RS109mConfig()

    # Instantiate DeviceConfigIO if a device is provided; otherwise use a dummy instance.
    if not mock and not device:
        raise ValueError("Must specify device if not using mock")

    device_io = MockDeviceIO() if mock else SerialDeviceIO(device)
    device_config_io = DeviceConfigIO(device_io)

    # load the current configuration from the device into config
    device_config_io.load_config(
        config=config,
        extended=extended,
        password=password,
        noread=noread,
    )

    # Print the current configuration (the hexadecimal dump is built inside DeviceConfigIO)
    typer.echo(
        f"Old configuration:\n{config.get_config_str(extended)}"
    )

    # Update configuration from provided CLI parameters.
    if mmsi is not None:
        config.mmsi = mmsi
    if name is not None:
        config.name = name
    if interval is not None:
        config.interval = interval
    if ship_type is not None:
        config.shipncargo = ship_type
    if callsign is not None:
        config.callsign = callsign
    if vendorid is not None:
        config.vendorid = vendorid
    if unitmodel is not None:
        config.unitmodel = unitmodel
    if sernum is not None:
        config.sernum = sernum
    if refa is not None:
        config.refa = refa
    if refb is not None:
        config.refb = refb
    if refc is not None:
        config.refc = refc
    if refd is not None:
        config.refd = refd

    # Print the current configuration (the hexadecimal dump is built inside DeviceConfigIO)
    typer.echo(
        f"Desired configuration:\n{config.get_config_str(extended)}"
    )

    # Write the configuration back to the device if requested.
    if device is not None and write:
        device_config_io.write_config(config, extended)

    # Re-read the configuration to confirm the new configuration has been applied
    updated_config = device_config_io.read_config(
        extended=extended,
        password=password,
        noread=noread,
    )
    # Print the current configuration (the hexadecimal dump is built inside DeviceConfigIO)
    typer.echo(
        f"Written configuration:\n{updated_config.get_config_str(extended)}"
    )


if __name__ == "__main__":
    app()
