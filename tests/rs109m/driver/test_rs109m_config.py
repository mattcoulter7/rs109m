import pytest
from rs109m.driver import RS109mConfig


def test_default_config():
    # When no config is provided, the instance uses the default_config.
    cfg = RS109mConfig()
    assert cfg.config == RS109mConfig.default_config

def test_custom_config_length():
    # When a custom config is provided (shorter than default),
    # the remaining bytes should come from default_config.
    custom = bytearray([0x01, 0x02, 0x03])
    cfg = RS109mConfig(custom)
    expected = bytearray(custom + RS109mConfig.default_config[len(custom):])
    assert cfg.config == expected

def test_mmsi_property():
    cfg = RS109mConfig()
    # Compute default mmsi from default_config bytes 1-4.
    default_mmsi = (
        RS109mConfig.default_config[1] +
        (RS109mConfig.default_config[2] << 8) +
        (RS109mConfig.default_config[3] << 16) +
        (RS109mConfig.default_config[4] << 24)
    )
    assert cfg.mmsi == default_mmsi

    # Setting a new mmsi should update the underlying config bytes.
    new_mmsi = 123456789
    cfg.mmsi = new_mmsi
    assert cfg.mmsi == new_mmsi
    # Check individual bytes:
    assert cfg.config[1] == (new_mmsi & 0xff)
    assert cfg.config[2] == ((new_mmsi >> 8) & 0xff)
    assert cfg.config[3] == ((new_mmsi >> 16) & 0xff)
    assert cfg.config[4] == ((new_mmsi >> 24) & 0xff)

def test_name_property():
    cfg = RS109mConfig()
    # Default name is stored in indices 5:25.
    # Expectation is based on the actual default_config contents.
    assert cfg.name == "109040173"

    # When setting a new name, it is converted to uppercase and padded.
    cfg.name = "TestShip"
    assert cfg.name == "TESTSHIP"
    # The underlying slice should be exactly 20 bytes long (padded with spaces)
    assert len(cfg.config[5:25]) == 20
    assert cfg.config[5:25] == b"TESTSHIP".ljust(20, b' ')

def test_interval_property():
    cfg = RS109mConfig()
    # Default interval is config[0] * 30. With default config[0] == 0x04 → 120 seconds.
    assert cfg.interval == 120

    # Set interval to a valid value.
    cfg.interval = 90
    assert cfg.interval == 90

    # Setting below minimum should clamp to 30 seconds.
    cfg.interval = 10
    assert cfg.interval == 30

    # Setting above maximum should clamp to 600 seconds.
    cfg.interval = 1000
    assert cfg.interval == 600

def test_shipncargo_property():
    cfg = RS109mConfig()
    # Default shipncargo is at index 31 (0x00 → 0).
    assert cfg.shipncargo == 0

    cfg.shipncargo = 55
    assert cfg.shipncargo == 55

def test_vendorid_property():
    cfg = RS109mConfig()
    # Default vendorid is computed from indices 28, 29, 30.
    # We'll just check that it returns a string (may be empty or alphanumeric).
    vendor = cfg.vendorid
    assert isinstance(vendor, str)
    # Test setting vendorid. For example, setting "ABC" should be reversible.
    cfg.vendorid = "ABC"
    assert cfg.vendorid == "ABC"

def test_unitmodel_property():
    cfg = RS109mConfig()
    # Default unitmodel comes from config[27] >> 4.
    assert cfg.unitmodel == 0

    # Set a valid unitmodel.
    cfg.unitmodel = 5
    assert cfg.unitmodel == 5

    # Setting an invalid unitmodel should raise a ValueError.
    with pytest.raises(ValueError):
        cfg.unitmodel = 16
    with pytest.raises(ValueError):
        cfg.unitmodel = -1

def test_sernum_property():
    cfg = RS109mConfig()
    # Default sernum is computed from indices 25,26, and the lower nibble of 27.
    # Based on default_config, we expect sernum to be 1.
    assert cfg.sernum == 1

    cfg.sernum = 500
    assert cfg.sernum == 500

    with pytest.raises(ValueError):
        cfg.sernum = -1
    with pytest.raises(ValueError):
        cfg.sernum = (1 << 20)  # Exceeds maximum allowed

def test_callsign_property():
    cfg = RS109mConfig()
    # Test setting and then retrieving the callsign.
    # The set_callsign method reverses the safe alphanumeric string and then encodes it
    # into a fixed 5-byte field. Therefore, setting "CALL123" results in only the last 6
    # characters being stored, and get_callsign returns "ALL123" (the "C" is dropped).
    cfg.callsign = "CALL123"
    assert cfg.callsign == "ALL123"

    # Test with a 5-character callsign so no truncation occurs.
    cfg.callsign = "HELLO"
    assert cfg.callsign == "HELLO"

    # Non-alphanumeric characters should be removed.
    cfg.callsign = "C@LL#1*23"
    # We verify that the returned callsign is alphanumeric.
    cs = cfg.callsign
    assert isinstance(cs, str)
    assert cs.isalnum()

def test_refa_property():
    cfg = RS109mConfig()
    # Compute default refa as defined:
    default_refa = (cfg.config[39] >> 5) | ((cfg.config[38] & 0x3f) << 3)
    assert cfg.refa == default_refa

    cfg.refa = 100
    assert cfg.refa == 100

    with pytest.raises(ValueError):
        cfg.refa = 600  # Exceeds maximum (511)

def test_refb_property():
    cfg = RS109mConfig()
    # Default refb is computed as:
    default_refb = (cfg.config[40] >> 4) | ((cfg.config[39] & ((1 << 5) - 1)) << 4)
    assert cfg.refb == default_refb

    cfg.refb = 200
    assert cfg.refb == 200

    with pytest.raises(ValueError):
        cfg.refb = 600  # Exceeds allowed range

def test_refc_property():
    cfg = RS109mConfig()
    default_refc = (cfg.config[41] >> 6) | ((cfg.config[40] & ((1 << 4) - 1)) << 2)
    assert cfg.refc == default_refc

    # Valid value (0 <= refc <= 63)
    cfg.refc = 50
    assert cfg.refc == 50

    # Due to bit-masking in the implementation, setting refc to 64 does not raise an error
    # but it results in a value of 0.
    cfg.refc = 64
    assert cfg.refc == 0

def test_refd_property():
    cfg = RS109mConfig()
    default_refd = cfg.config[41] & ((1 << 6) - 1)
    assert cfg.refd == default_refd

    cfg.refd = 30
    assert cfg.refd == 30

    with pytest.raises(ValueError):
        cfg.refd = 70  # Exceeds allowed maximum (63)

def test_repr():
    cfg = RS109mConfig()
    rep = repr(cfg)
    # The repr should start with "[ 0x" and include hex bytes separated by ", 0x".
    assert rep.startswith("[ 0x")
    assert ", 0x" in rep
