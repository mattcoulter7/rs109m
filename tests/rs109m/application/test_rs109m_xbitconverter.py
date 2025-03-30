import pytest
from rs109m.xbitconverter import toxbit, fromxbit

# ----------------------------
# Tests for fromxbit function
# ----------------------------

def test_fromxbit_invalid_bit_length():
    # Bit length out of allowed range should raise ValueError.
    with pytest.raises(ValueError):
        fromxbit(bytearray([0xff]), x=0)
    with pytest.raises(ValueError):
        fromxbit(bytearray([0xff]), x=8)

def test_fromxbit_empty_array():
    # Supplying an empty array should raise ValueError.
    with pytest.raises(ValueError):
        fromxbit(bytearray(), x=6)

def test_fromxbit_conversion_digitalpha():
    # Use an input that will trigger the digitalphaencoding adjustment.
    # For bytearray([0x01, 0x00]) with x=6:
    #  - i=0: (0x01 & 0x3f) = 1, but since digitalphaencoding is True and 1 is non-zero and not a digit,
    #    it is transformed to (1 | 0x40) = 65.
    #  - i=1: yields 0.
    result = fromxbit(bytearray([0x01, 0x00]), x=6, digitalphaencoding=True)
    expected = bytearray([65, 0])
    assert result == expected

def test_fromxbit_conversion_no_digitalpha():
    # With digitalphaencoding disabled the value remains unmodified.
    # For the same input, i=0 yields 1 and i=1 yields 0.
    result = fromxbit(bytearray([0x01, 0x00]), x=6, digitalphaencoding=False)
    expected = bytearray([1, 0])
    assert result == expected

def test_fromxbit_conversion_x7():
    # Test with x=7. For a simple input, the conversion should leave the value unchanged.
    # Using input bytearray([65]) (ASCII for 'A'):
    result = fromxbit(bytearray([65]), x=7, digitalphaencoding=False)
    expected = bytearray([65])
    assert result == expected

# ----------------------------
# Tests for toxbit function
# ----------------------------

def test_toxbit_invalid_bit_length():
    # Bit length out of allowed range should raise ValueError.
    with pytest.raises(ValueError):
        toxbit("A", x=0)
    with pytest.raises(ValueError):
        toxbit("A", x=8)

def test_toxbit_empty_input():
    # When given an empty input (as a string), toxbit returns a fixed list.
    result = toxbit("", x=6)
    expected = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
    assert result == expected

def test_toxbit_conversion_string():
    # When digitalphaencoding is True and input is a string, the function first converts it to uppercase.
    # For "A", ASCII code is 65; then 65 & ((1<<6)-1) = 65 & 63 = 1.
    result = toxbit("A", x=6, digitalphaencoding=True)
    expected = bytearray([1])
    assert result == expected

def test_toxbit_conversion_bytearray():
    # When providing a bytearray and with digitalphaencoding disabled, no conversion of case occurs.
    # For input 0xff, with x=6, we get: 0xff & 63 = 63.
    result = toxbit(bytearray([0xff]), x=6, digitalphaencoding=False)
    expected = bytearray([63])
    assert result == expected

def test_toxbit_conversion_x7():
    # Test toxbit with bit length 7 on a string.
    # For "A" with x=7, the conversion does:
    #   65 & ((1<<7)-1) = 65 & 127 = 65.
    result = toxbit("A", x=7, digitalphaencoding=True)
    expected = bytearray([65])
    assert result == expected
