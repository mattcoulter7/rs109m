import typer
import logging
from typing import Optional
from enum import Enum

from rs109m.driver_service.models import (
    RS109mReadConfigRequest,
    RS109mWriteConfigRequest,
    RS109mConfig,
)
from rs109m.driver_service.ship_type import ShipType
from rs109m.driver_service.service import RS109mConfigurationService
from rs109m.application.cli.validate import (
    validate_interval, validate_vendorid, validate_unitmodel, 
    validate_sernum, validate_refa, validate_refb, 
    validate_refc, validate_refd, validate_password,
    validate_callsign,
)

logger = logging.getLogger(__name__)
service = RS109mConfigurationService()
app = typer.Typer()

class Mode(str, Enum):
    read = "read"
    write = "write"

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    mode: Optional[Mode] = typer.Option(None, "--mode", "-m")
):
    if ctx.invoked_subcommand is None:
        if not mode:
            mode = typer.prompt(
                f"Choose mode [{','.join([_.value for _ in Mode])}]",
                type=Mode,
            )
        app([mode.value])


@app.command("read")
def read_config(
    device: str = typer.Option(
        ...,
        "--device",
        "-d",
        help="Serial port (e.g. /dev/ttyUSB0)"
    ),
    password: Optional[str] = typer.Option(
        None,
        "--password",
        "-P",
        help="Password (leave blank for default)",
        callback=validate_password,
        show_default=False,
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
    config = service.read_config(
        RS109mReadConfigRequest(
            device=device,
            mock=mock,
            password=password,
            extended=extended
        )
    )

    typer.echo(f"Read configuration:\n{config.get_config_str()}")

    # simple approach to prevent the window from closing immediately
    typer.prompt("Press Enter to exit...", default="", show_default=False)


@app.command("write")
def write_config(
    device: str = typer.Option(
        ...,
        "--device",
        "-d",
        help="Serial port device (e.g. /dev/ttyUSB0) (leave blank for default config)",
    ),
    password: Optional[str] = typer.Option(
        None,
        "--password",
        "-P",
        help="Password (leave blank for default)",
        callback=validate_password
    ),
    mmsi: Optional[int] = typer.Option(
        None,
        "--mmsi",
        "-m",
        help="MMSI (leave blank to keep current configuration)",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Ship name (leave blank to keep current configuration)",
    ),
    interval: Optional[int] = typer.Option(
        None,
        "--interval",
        "-i",
        help="Transmit interval in seconds [30..600] (leave blank to keep current configuration)",
        callback=validate_interval
    ),
    ship_type: Optional[int] = typer.Option(
        None,
        "--type",
        "-t",
        help="Ship type (leave blank to keep current configuration)",
    ),
    callsign: Optional[str] = typer.Option(
        None,
        "--callsign",
        "-c",
        help="Call sign (max 6 characters; leave blank to keep current configuration)",
        callback=validate_callsign
    ),
    refa: Optional[int] = typer.Option(
        None,
        "--refa",
        "-A",
        help="Reference A (leave blank to keep current configuration)",
        callback=validate_refa
    ),
    refb: Optional[int] = typer.Option(
        None,
        "--refb",
        "-B",
        help="Reference B (leave blank to keep current configuration)",
        callback=validate_refb
    ),
    refc: Optional[int] = typer.Option(
        None,
        "--refc",
        "-C",
        help="Reference C (leave blank to keep current configuration)",
        callback=validate_refc
    ),
    refd: Optional[int] = typer.Option(
        None,
        "--refd",
        "-D",
        help="Reference D (leave blank to keep current configuration)",
        callback=validate_refd
    ),
    vendorid: Optional[str] = typer.Option(
        None,
        "--vendorid",
        "-v",
        help="AIS unit vendor id (3 characters) (leave blank to keep current configuration)",
        callback=validate_vendorid
    ),
    unitmodel: Optional[int] = typer.Option(
        None,
        "--unitmodel",
        "-u",
        help="AIS unit vendor model code (leave blank to keep current configuration)",
        callback=validate_unitmodel
    ),
    sernum: Optional[int] = typer.Option(
        None,
        "--sernum",
        "-s",
        help="AIS unit serial num (leave blank to keep current configuration)",
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
    config = service.write_config(
        RS109mWriteConfigRequest(
            config=RS109mConfig(
                mmsi=mmsi,
                name=name,
                interval=interval,
                ship_type=ShipType(ship_type),
                callsign=callsign,
                vendorid=vendorid,
                unitmodel=unitmodel,
                sernum=sernum,
                refa=refa,
                refb=refb,
                refc=refc,
                refd=refd,
            ),
            device=device,
            mock=mock,
            password=password,
            extended=extended
        )
    )

    # Print the current configuration (the hexadecimal dump is built inside DeviceConfigIO)
    typer.echo(
        f"Writen configuration:\n{config.get_config_str()}"
    )

    # simple approach to prevent the window from closing immediately
    typer.prompt("Press Enter to exit...", default="", show_default=False)


if __name__ == "__main__":
    app()
