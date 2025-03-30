import typer
import logging
from typing import Optional

from rs109m.driver import RS109mDriver
from rs109m.driver.constants import DEFAULT_PASSWORD
from rs109m.driver.device_io import SerialDeviceIO, MockDeviceIO
from rs109m.application.cli.validate import (
    validate_interval, validate_vendorid, validate_unitmodel, 
    validate_sernum, validate_refa, validate_refb, 
    validate_refc, validate_refd, validate_password,
    validate_callsign,
)

logger = logging.getLogger(__name__)
app = typer.Typer(no_args_is_help=True)


def get_driver(device: Optional[str], mock: bool) -> RS109mDriver:
    if not mock and not device:
        raise ValueError("Must specify device if not using mock")
    device_io = MockDeviceIO() if mock else SerialDeviceIO(device)
    return RS109mDriver(device_io)


@app.command("read")
def read_config(
    device: str = typer.Option(
        ...,
        "--device",
        "-d",
        help="Serial port (e.g. /dev/ttyUSB0)",
        prompt="Enter serial port device"
    ),
    password: Optional[str] = typer.Option(
        DEFAULT_PASSWORD,
        "--password",
        "-P",
        help="Password (leave blank for default)",
        prompt="Enter password (leave blank for default)",
        callback=validate_password
    ),
    mock: bool = typer.Option(
        False,
        "--mock",
        help="Use the mock device IO instead of a real device"
    ),
    extended: bool = typer.Option(
        False,
        "--extended",
        "-E",
        help="Operate on 0xff size config instead of default 0x40"
    )
):
    driver = get_driver(device, mock)
    config = driver.read_config(password=password, extended=extended)
    typer.echo(f"Read configuration:\n{config.get_config_str(extended)}")


@app.command("write")
def write_config(
    device: str = typer.Option(
        ...,
        "--device",
        "-d",
        help="Serial port device (e.g. /dev/ttyUSB0) (leave blank for default config)",
        prompt="Enter serial port device"
    ),
    password: Optional[str] = typer.Option(
        DEFAULT_PASSWORD,
        "--password",
        "-P",
        help="Password (leave blank for default)",
        prompt="Enter password (leave blank for default)",
        callback=validate_password
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
        prompt="Enter transmit interval in seconds (leave blank to keep current configuration)",
        callback=validate_interval
    ),
    ship_type: Optional[int] = typer.Option(
        None,
        "--type",
        "-t",
        help="Ship type (leave blank to keep current configuration)",
        prompt="Enter ship type (leave blank to keep current configuration)"
    ),
    callsign: Optional[str] = typer.Option(
        None,
        "--callsign",
        "-c",
        help="Call sign (max 6 characters; leave blank to keep current configuration)",
        prompt="Enter call sign (max 6 characters; leave blank to keep current configuration)",
        callback=validate_callsign
    ),
    refa: Optional[int] = typer.Option(
        None,
        "--refa",
        "-A",
        help="Reference A (leave blank to keep current configuration)",
        prompt="Enter Reference A (leave blank to keep current configuration)",
        callback=validate_refa
    ),
    refb: Optional[int] = typer.Option(
        None,
        "--refb",
        "-B",
        help="Reference B (leave blank to keep current configuration)",
        prompt="Enter Reference B (leave blank to keep current configuration)",
        callback=validate_refb
    ),
    refc: Optional[int] = typer.Option(
        None,
        "--refc",
        "-C",
        help="Reference C (leave blank to keep current configuration)",
        prompt="Enter Reference C (leave blank to keep current configuration)",
        callback=validate_refc
    ),
    refd: Optional[int] = typer.Option(
        None,
        "--refd",
        "-D",
        help="Reference D (leave blank to keep current configuration)",
        prompt="Enter Reference D (leave blank to keep current configuration)",
        callback=validate_refd
    ),
    vendorid: Optional[str] = typer.Option(
        None,
        "--vendorid",
        "-v",
        help="AIS unit vendor id (3 characters) (leave blank to keep current configuration)",
        prompt="Enter vendor id (leave blank to keep current configuration)",
        callback=validate_vendorid
    ),
    unitmodel: Optional[int] = typer.Option(
        None,
        "--unitmodel",
        "-u",
        help="AIS unit vendor model code (leave blank to keep current configuration)",
        prompt="Enter vendor model code (leave blank to keep current configuration)",
        callback=validate_unitmodel
    ),
    sernum: Optional[int] = typer.Option(
        None,
        "--sernum",
        "-s",
        help="AIS unit serial num (leave blank to keep current configuration)",
        prompt="Enter serial number (leave blank to keep current configuration)",
        callback=validate_sernum
    ),
    mock: bool = typer.Option(
        False,
        "--mock",
        help="Use the mock device IO instead of a real device"
    ),
    extended: bool = typer.Option(
        False,
        "--extended",
        "-E",
        help="Operate on 0xff size config instead of default 0x40"
    )
):
    driver = get_driver(device, mock)

    # read the current configuration from the device into config
    config = driver.read_config(
        password=password,
        extended=extended,
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
    driver.write_config(
        config,
        password=password,
        extended=extended,
    )

    # Re-read the configuration to confirm the new configuration has been applied
    updated_config = driver.read_config(
        password=password,
        extended=extended,
    )

    # Print the current configuration (the hexadecimal dump is built inside DeviceConfigIO)
    typer.echo(
        f"Written configuration:\n{updated_config.get_config_str(extended)}"
    )


if __name__ == "__main__":
    app()
