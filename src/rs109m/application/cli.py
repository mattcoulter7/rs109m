import argparse
import serial
import re
import logging

from rs109m.config import RS109mConfig
from rs109m.constants import DEFAULT_PASSWORD, BAUDRATE, PASSWORD_MAXLEN

logger = logging.getLogger(__name__)


def main():
    # TODO: probably refactor this to use typer or some other cli framework
    parser = argparse.ArgumentParser(description = 'RS-109M Net Locator AIS buoy configurator')
    parser.add_argument("-d", "--device", help="serial port device (e.g. /dev/ttyUSB0)")
    parser.add_argument("-m", "--mmsi", help="MMSI")
    parser.add_argument("-n", "--name", help="ship name")
    parser.add_argument("-i", "--interval", help="transmit interval in s [30..600]")
    parser.add_argument("-t", "--type", help="ship type, eg sail=36, pleasure craft=37")
    parser.add_argument("-c", "--callsign", help="call sign")
    parser.add_argument("-v", "--vendorid", help="AIS unit vendor id (3 characters)")
    parser.add_argument("-u", "--unitmodel", help="AIS unit vendor model code")
    parser.add_argument("-s", "--sernum", help="AIS unit serial num")
    parser.add_argument("-A", "--refa", help="Reference A (distance AIS to bow (m); Net Locator sends battery voltage instead)")
    parser.add_argument("-B", "--refb", help="Reference B (distance AIS to stern (m)")
    parser.add_argument("-C", "--refc", help="Reference C (distance AIS to port (m)")
    parser.add_argument("-D", "--refd", help="Reference D (distance AIS to starboard (m)")
    default_password = DEFAULT_PASSWORD
    parser.add_argument("-P", "--password", help="password to access Net Locator")
    parser.add_argument("-E", "--extended", help="operate on 0xff size config instead of default 0x40", action='store_true')
    # parser.add_argument("-P", "--newpass", help="set new password to access Net Locator")
    parser.add_argument("-W", "--write", help="write config to Net Locator", action='store_true')
    parser.add_argument("-R", "--noread", help="do not read from Net Locator", action='store_true')
    args = parser.parse_args()

    c = RS109mConfig()
    num_bytes = c.default_len
    if args.extended:
        num_bytes = 0xff

    ser = None

    if args.device != None:
        ser = serial.Serial()
        ser.port = args.device

        ser.baudrate = BAUDRATE
        ser.bytesize = serial.EIGHTBITS
        ser.parity = serial.PARITY_NONE
        ser.stopbits = serial.STOPBITS_ONE

        ser.timeout = 1
        ser.write_timeout = 3

        ser.open()

        # try read and timeout seems to make more reliable connection
        ser.read(0xffff)
        ser.timeout = 3

        if args.password != None:
            password = args.password

            password_maxlen = PASSWORD_MAXLEN

            if not re.match("^[0-9]{0,"+str(password_maxlen)+"}$", password):
                logger.error("Password: incorrect format, should match [0-9]{0,"+str(password_maxlen)+"}")
                exit(1)

            password_prepared = (password.encode() + default_password.encode())[:password_maxlen]
            ser.write([0x59, 0x01, 0x42, password_maxlen])
            ser.write(password_prepared)
        else:
            # This seems to work even with a password set
            ser.write([0x59, 0x01, 0x42, 0x00])

        r = ser.read(2)

        if r != b'\x95\x20':
            logger.error('Could not initialize with password.')
            exit(1)

        if args.noread == False:
            ser.write([0x51, num_bytes])
            r = ser.read(2)
            if r != bytes([0x25, num_bytes]):
                logger.error("Could not read config, got this instead:")
                logger.debug(r.hex(' '))
                exit(1)

            config = ser.read(num_bytes)
            if len(config) == num_bytes:
                c.config = config
            else:
                logger.error("Could not read config from device")
                exit(1)
    else:
        logger.info('Operating on default config:')
        logger.info()

    if args.mmsi != None:
        c.mmsi = args.mmsi

    if args.name != None:
        c.name = args.name

    if args.interval != None:
        c.interval = args.interval

    if args.type != None:
        c.shipncargo = args.type

    if args.callsign != None:
        c.callsign = args.callsign

    if args.vendorid!= None:
        c.vendorid = args.vendorid

    if args.unitmodel != None:
        c.unitmodel = args.unitmodel

    if args.sernum!= None:
        c.sernum= args.sernum

    if args.refa != None:
        c.refa = int(args.refa)

    if args.refb != None:
        c.refb = int(args.refb)

    if args.refc != None:
        c.refc = int(args.refc)

    if args.refd != None:
        c.refd = int(args.refd)

    logger.info('  MMSI: %(mmsi)s' % {'mmsi': c.mmsi})
    logger.info('  Name: %(name)s' % {'name': c.name})
    logger.info('  TX interval (s): %(interval)d' % {'interval': c.interval})
    logger.info('  Ship type: %(shipncargo)s' % {'shipncargo': c.shipncargo})
    logger.info('  Callsign: %(callsign)s' % {'callsign': c.callsign})
    logger.info('  VendorID: %(vendorid)s' % {'vendorid': c.vendorid})
    logger.info('  UnitModel: %(unitmodel)d' % {'unitmodel': c.unitmodel})
    logger.info('  UnitSerial: %(sernum)d' % {'sernum': c.sernum})
    logger.info('  Reference point A (m): {:d} (read-only battery voltage {:.1f}V)' .format(c.refa, c.refa/10.00))
    logger.info('  Reference point B (m): %(refb)d' % {'refb': c.refb})
    logger.info('  Reference point C (m): %(refc)d' % {'refc': c.refc})
    logger.info('  Reference point D (m): %(refd)d' % {'refd': c.refd})
    logger.info()
    logger.info('[ 0x' + c.config[:num_bytes].hex('#').replace('#',', 0x') + ' ]')

    if args.device != None and args.write:
        ser.write([0x55, num_bytes])
        ser.write(c.config[:num_bytes])

        r = ser.read(2)
        if r != bytes([0x75, num_bytes]):
            logger.error("Write failed")
            exit(1)
        else:
            logger.info('Config written successfully!')
    else:
        if args.write:
            logger.error('Must supply serial device with -d option.')
            exit(1)


if __name__ == "__main__":
    main()
