from .models import RS109mConfig

from rs109m.driver import RS109mRawConfig


def apply_rs109m_config_to_driver_config(
    config: RS109mConfig,
    driver_config: RS109mRawConfig
) -> None:
    """Apply values from pydantic RS109mConfig to one that is understood by the RS109m driver"""
    if config.mmsi is not None:
        driver_config.mmsi = config.mmsi
    if config.name is not None:
        driver_config.name = config.name
    if config.interval is not None:
        driver_config.interval = config.interval
    if config.ship_type is not None:
        driver_config.shipncargo = config.ship_type.value
    if config.callsign is not None:
        driver_config.callsign = config.callsign
    if config.vendorid is not None:
        driver_config.vendorid = config.vendorid
    if config.unitmodel is not None:
        driver_config.unitmodel = config.unitmodel
    if config.sernum is not None:
        driver_config.sernum = config.sernum
    if config.refa is not None:
        driver_config.refa = config.refa
    if config.refb is not None:
        driver_config.refb = config.refb
    if config.refc is not None:
        driver_config.refc = config.refc
    if config.refd is not None:
        driver_config.refd = config.refd
    return None

def driver_config_to_rs109m_config(config: RS109mRawConfig) -> RS109mConfig:
    """Convert the RS109m driver read configuration back to pydantic schema version"""
    return RS109mConfig(
        mmsi=config.mmsi,
        name=config.name,
        interval=config.interval,
        ship_type=config.shipncargo,
        callsign=config.callsign,
        vendorid=config.vendorid,
        unitmodel=config.unitmodel,
        sernum=config.sernum,
        refa=config.refa,
        refb=config.refb,
        refc=config.refc,
        refd=config.refd,
    )
