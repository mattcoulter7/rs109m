def fromxbit(ba, x=6, digitalphaencoding=True):
    if ((x < 1) or (x > 7)):
        raise ValueError("BitLen must between 1 and 7")
    if len(ba) < 1:
        raise ValueError("Must supply non-empty array")

    n = len(ba) * 8 // x
    b = bytearray([0 for i in range(n)])

    for i in range(n):
        pos = i * x // 8
        shift = i * x % 8

        b[i] = (ba[pos] >> shift) & ((1 << x) - 1)
        remaining = shift + x - 8
        if remaining > 0:
            b[i] |= (ba[pos + 1] << (8 - shift)) & ((1 << x) - 1)
        if digitalphaencoding and (b[i] & 0x20) != 0x20 and b[i] != 0:
            # not a digit, is alpha
            b[i] = (b[i] & 0x1f) | 0x40

    return b


def toxbit(ba, x=6, digitalphaencoding=True):
    if ((x < 1) or (x > 7)):
        raise ValueError("BitLen must between 1 and 7")
    if len(ba) < 1:
        return [0xff, 0xff, 0xff, 0xff, 0xff, 0xff]

    if digitalphaencoding:
        ba = bytearray(
            ba.encode('ascii', 'ignore').decode().upper().encode('ascii'))

    n = len(ba) * x // 8
    if (len(ba) * x % 8) > 0:
        n += 1
    if n == 0:
        n = 1
    b = bytearray([0 for i in range(n)])

    for i in range(len(ba)):
        pos = i * x // 8
        shift = i * x % 8

        ba[i] = ba[i] & ((1 << x) - 1)

        b[pos] |= (ba[i] << shift) & 0xff
        remaining = shift + x - 8
        # print(ba[i], " i=", i, " pos=", pos, " shift=", shift, " remaining=", remaining)
        if remaining > 0:
            b[pos + 1] |= (ba[i] >> (8 - shift))
    return b
