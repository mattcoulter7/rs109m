import pytest
from typer.testing import CliRunner

from rs109m.application.cli import app
from rs109m.driver import RS109mConfig
from rs109m.driver.device_io import MockDeviceIO

runner = CliRunner()


def test_cli_update_config_with_mock():
    # Provide every parameter so that no prompt is triggered.
    args = [
        "--device", "dummy_device",  # device is a dummy string here
        "--mock",
        "--mmsi", "123456789",
        "--name", "TEST SHIP",
        "--interval", "30",
        "--type", "36",
        "--callsign", "TSALL",
        "--vendorid", "ABC",
        "--unitmodel", "1",
        "--sernum", "1234",
        "--refa", "10",
        "--refb", "20",
        "--refc", "30",
        "--refd", "40",
        "--password", "123",
    ]
    
    result = runner.invoke(app, args)
    
    assert result.exit_code == 0
    # Check that the output contains our updated configuration values.
    assert "123456789" in result.output
    assert "TEST SHIP" in result.output
    assert "30" in result.output
    assert "36" in result.output
    assert "TSALL" in result.output
