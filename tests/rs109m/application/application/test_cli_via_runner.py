import pytest
from typer.testing import CliRunner
from rs109m.application.cli import app
from rs109m.device_io import MockDeviceIO
from rs109m.config import RS109mConfig

runner = CliRunner()

@pytest.fixture(autouse=True)
def patch_mock_initial_read(monkeypatch):
    def custom_get_initial_read_data(self):
        config = RS109mConfig()
        size = config.default_len
        return (
            b'\x95\x20' +                   # Handshake response
            bytes([0x25, size]) +          # Config read ack
            config.config[:size]           # Config block
        )

    monkeypatch.setattr(MockDeviceIO, "get_initial_read_data", custom_get_initial_read_data)

def test_cli_update_config_with_mock():
    # Provide every parameter so that no prompt is triggered.
    args = [
        "--device", "dummy_device",  # device is a dummy string here
        "--mock",
        "--mmsi", "123456789",
        "--name", "TEST SHIP",
        "--interval", "30",
        "--type", "36",
        "--callsign", "CALL",
        "--vendorid", "ABC",
        "--unitmodel", "1",
        "--sernum", "1234",
        "--refa", "10",
        "--refb", "20",
        "--refc", "30",
        "--refd", "40",
        "--password", "123",
        "--noread"  # Avoid extended reading during the test
    ]
    
    result = runner.invoke(app, args)
    
    assert result.exit_code == 0
    # Check that the output contains our updated configuration values.
    assert "123456789" in result.output
    assert "TEST SHIP" in result.output
    assert "30" in result.output
    assert "36" in result.output
    assert "CALL" in result.output
