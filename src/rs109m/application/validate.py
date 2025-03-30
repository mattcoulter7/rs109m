import re
import typer
from typing import Optional

def validate_vendorid(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    if len(value) > 3:
        raise typer.BadParameter("VendorID must be at most 3 characters.")
    return value

def validate_unitmodel(value: Optional[int]) -> Optional[int]:
    if value is None:
        return value
    if value < 0 or value > 15:
        raise typer.BadParameter("Unit model must be between 0 and 15.")
    return value

def validate_sernum(value: Optional[int]) -> Optional[int]:
    if value is None:
        return value
    if value < 0 or value > 1048575:
        raise typer.BadParameter("Serial number must be between 0 and 1048575.")
    return value

def validate_refa(value: Optional[int]) -> Optional[int]:
    if value is None:
        return value
    if value < 0 or value > 511:
        raise typer.BadParameter("Reference A must be between 0 and 511.")
    return value

def validate_refb(value: Optional[int]) -> Optional[int]:
    if value is None:
        return value
    if value < 0 or value > 511:
        raise typer.BadParameter("Reference B must be between 0 and 511.")
    return value

def validate_refc(value: Optional[int]) -> Optional[int]:
    if value is None:
        return value
    if value < 0 or value > 63:
        raise typer.BadParameter("Reference C must be between 0 and 63.")
    return value

def validate_refd(value: Optional[int]) -> Optional[int]:
    if value is None:
        return value
    if value < 0 or value > 63:
        raise typer.BadParameter("Reference D must be between 0 and 63.")
    return value

def validate_password(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    if not re.fullmatch(r"[0-9]{0,6}", value):
        raise typer.BadParameter("Password must be 0 to 6 digits.")
    return value

def validate_interval(value: Optional[int]) -> Optional[int]:
    if value is None:
        return value
    if value < 30 or value > 600:
        raise typer.BadParameter("Interval must be between 30 and 600 seconds.")
    return value
