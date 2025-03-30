from .xbitconverter import fromxbit, toxbit


class RS109mRawConfig:
    default_config = bytearray([
        0x04, 0x2d, 0xd2, 0x7f, 0x06, 0x31, 0x30, 0x39, 0x30, 0x34, 0x30, 0x31, 0x37, 0x33, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x01, 0x00, 0x00, 0xe0, 0x24, 0x01, 0x00,
        0x35, 0x3d, 0xcb, 0xf1, 0x23, 0x00, 0x08, 0xa0, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,

        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff
    ])
    default_len = 0x40

    def __init__(self):
        self.set_config([])

    def get_config(self):
        return self._config

    def set_config(self, config):
        # TODO: implement differently, as setting config as slices config[34:38] might be convenient
        if config == []:
            # self._config = self.default_config[:self.default_len]
            self._config = self.default_config[:]  # [:] creates a copy, ensuring data doesn't persistent across multiple objects
        else:
            clen = 0xff if (len(config) > 0xff) else len(config)
            self._config = bytearray(
                config[0:clen] + self.default_config[clen:])

    config = property(get_config, set_config)

    def get_mmsi(self):
        mmsi = self._config[1] + (self._config[2] << 8) + \
            (self._config[3] << 16) + ((self._config[4] & 0xff) << 24)
        return mmsi

    def set_mmsi(self, mmsi):
        mmsi = int(mmsi)
        self._config[1] = mmsi & 0xff
        self._config[2] = (mmsi >> 8) & 0xff
        self._config[3] = (mmsi >> 16) & 0xff
        self._config[4] = (mmsi >> 24) & 0xff

    mmsi = property(get_mmsi, set_mmsi)

    def get_name(self):
        name = bytes(self._config[5:25]).decode('ascii').strip()
        return name

    def set_name(self, name):
        # TODO: check for invalid chars, this one is incomplete
        safe_name = name.encode('ascii', 'ignore').decode(
        ).upper().ljust(20, ' ').encode('ascii')
        self._config[5:25] = safe_name

    name = property(get_name, set_name)

    def __repr__(self):
        return '[ 0x' + self._config.hex('#').replace('#', ', 0x') + ' ]'

    def get_interval(self):
        return self._config[0] * 30

    def set_interval(self, seconds):
        seconds = int(seconds)
        if seconds > 600:
            seconds = 600
        if seconds < 30:
            seconds = 30
        self._config[0] = seconds//30

    interval = property(get_interval, set_interval)

    def get_shipncargo(self):
        return int(self._config[31])

    def set_shipncargo(self, shiptype):
        self._config[31] = int(shiptype) & 0xff

    shipncargo = property(get_shipncargo, set_shipncargo)

    def get_vendorid(self):
        vid = [(self._config[29] >> 4) | ((self._config[30] & 0x03) << 4) | 0x40,
               (self._config[28] >> 6) | (
                   (self.config[29] & 0x07) << 2) | 0x40,
               (self._config[28] & 0x3f) | 0x40]
        return ''.join(c if c.isalnum() else '' for c in bytes(vid).decode())

    def set_vendorid(self, vid):
        # TODO: check for invalid chars, this one is incomplete
        safe_vid = vid.encode('ascii', 'ignore').decode(
        ).upper().ljust(3, '\x00')[:3].encode('ascii')
        print(safe_vid)
        self._config[28] = (safe_vid[2] & 0x3f) | ((safe_vid[1] << 6) & 0xff)
        self._config[29] = ((safe_vid[1] >> 2) & 0x0f) | (
            (safe_vid[0] << 4) & 0xff)
        self._config[30] = (self._config[30] & ~0x0f) | (
            (safe_vid[0] & 0x3f) >> 4)

    vendorid = property(get_vendorid, set_vendorid)

    def get_unitmodel(self):
        unitmodel = self._config[27] >> 4
        return unitmodel

    def set_unitmodel(self, unitmodel):
        unitmodel = int(unitmodel)
        if unitmodel < 0 or unitmodel > 15:
            raise ValueError("UnitModel must be 0 < unitmodel <= 15")
        self._config[27] = (self._config[27] & 0xf0) | (
            (int(unitmodel) & 0x0f) << 4)

    unitmodel = property(get_unitmodel, set_unitmodel)

    def get_sernum(self):
        sernum = self._config[25] + (self._config[26]
                                     << 8) + ((self._config[27] & 0x0f) << 16)
        return sernum

    def set_sernum(self, sernum):
        sernum = int(sernum)
        if sernum < 0 or sernum > ((1 << 20) - 1):
            raise ValueError(
                "UnitSernum must be 0 <= sernum <=", ((1 << 20) - 1))
        self._config[25] = sernum & 0xff
        self._config[26] = (sernum >> 8) & 0xff
        self._config[27] = (self._config[27] & 0xf0) | ((sernum >> 16) & 0x0f)

    sernum = property(get_sernum, set_sernum)

    def get_callsign(self):
        # TODO: check if it is 32:37 or 32:38
        s = fromxbit(self._config[32:37], 6, True).decode('ascii')[::-1]
        return ''.join(c if c.isalnum() else '' for c in s)

    def set_callsign(self, cs):
        safe_cs = ''.join(c if c.isalnum() else '' for c in cs)
        self._config[32:37] = toxbit(safe_cs[::-1])

    callsign = property(get_callsign, set_callsign)

    def get_refa(self):
        return (self._config[39] >> 5) | ((self.config[38] & ((1 << 6) - 1)) << 3)

    def set_refa(self, a):
        if int(a) > (1 << 9):
            raise ValueError("Reference a must be <= 511")
        if int(a) < 0:
            raise ValueError("Reference a must be >= 0")
        self._config[39] = (self._config[39] & ((1 << 5) - 1)
                            ) | (((int(a) & ((1 << 6) - 1)) << 5) & 0xff)
        self._config[38] = (self._config[38] & ~(
            (1 << 4) - 1)) | ((int(a) & ((1 << 9) - 1)) >> 3)

    refa = property(get_refa, set_refa)

    def get_refb(self):
        return (self._config[40] >> 4) | ((self._config[39] & ((1 << 5) - 1)) << 4)

    def set_refb(self, b):
        if int(b) > (1 << 9):
            raise ValueError("Reference b must be <= 511")
        if int(b) < 0:
            raise ValueError("Reference b must be >= 0")
        self._config[40] = (self._config[40] & ((1 << 4) - 1)
                            ) | (((int(b) & ((1 << 6) - 1)) << 4) & 0xff)
        self._config[39] = (self._config[39] & ~(
            (1 << 5) - 1)) | ((int(b) & ((1 << 9) - 1)) >> 4)

    refb = property(get_refb, set_refb)

    def get_refc(self):
        return (self._config[41] >> 6) | ((self._config[40] & ((1 << 4) - 1)) << 2)

    def set_refc(self, c):
        if int(c) > (1 << 6):
            raise ValueError("Reference c must be <= 63")
        if int(c) < 0:
            raise ValueError("Reference c must be >= 0")
        self._config[41] = (self._config[41] & ((1 << 6) - 1)
                            ) | (((int(c) & ((1 << 6) - 1)) << 6) & 0xff)
        self._config[40] = (self._config[40] & ~(
            (1 << 4) - 1)) | ((int(c) & ((1 << 6) - 1)) >> 2)

    refc = property(get_refc, set_refc)

    def get_refd(self):
        return self._config[41] & ((1 << 6) - 1)

    def set_refd(self, d):
        if int(d) > (1 << 6):
            raise ValueError("Reference d must be <= 63")
        if int(d) < 0:
            raise ValueError("Reference d must be >= 0")
        self._config[41] = (self._config[41] & ~(
            (1 << 6) - 1)) | (int(d) & ((1 << 6) - 1))

    refd = property(get_refd, set_refd)

    def get_config_str(
        self,
        extended: bool,
    ) -> str:
        """
        Returns a string representation of the configuration.
        """
        num_bytes = self.default_len
        if extended:
            num_bytes = 0xff

        out = []
        out.append(f"  MMSI: {self.mmsi}")
        out.append(f"  Name: {self.name}")
        out.append(f"  TX interval (s): {self.interval}")
        out.append(f"  Ship type: {self.shipncargo}")
        out.append(f"  Callsign: {self.callsign}")
        out.append(f"  VendorID: {self.vendorid}")
        out.append(f"  UnitModel: {self.unitmodel}")
        out.append(f"  UnitSerial: {self.sernum}")
        out.append(f"  Reference point A (m): {self.refa} (read-only battery voltage {self.refa/10.0:.1f}V)")
        out.append(f"  Reference point B (m): {self.refb}")
        out.append(f"  Reference point C (m): {self.refc}")
        out.append(f"  Reference point D (m): {self.refd}")
        out.append("")
        out.append("[ 0x" + self.config[:num_bytes].hex('#').replace('#', ', 0x') + " ]")

        return "\n".join(out)
