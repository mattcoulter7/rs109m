from typer.testing import CliRunner

from rs109m.application.cli import app

runner = CliRunner()



def test_cli_read():
    # Provide every parameter so that no prompt is triggered.
    args = [
        "read",
        "--mock",
        "--device", "dummy_device",
        "--password", "123",
    ]
    
    result = runner.invoke(app, args)
    
    assert result.exit_code == 0

def test_cli_write():
    # Provide every parameter so that no prompt is triggered.
    args = [
        "write",
        "--mock",
        "--device", "dummy_device",  # device is a dummy string here
        "--password", "123",
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
    ]
    
    result = runner.invoke(app, args)
    
    assert result.exit_code == 0
    # Check that the output contains our updated configuration values.
    assert "123456789" in result.output
    assert "TEST SHIP" in result.output
    assert "30" in result.output
    assert "ShipType.SAILING" in result.output  # this is from 36
    assert "TSALL" in result.output
