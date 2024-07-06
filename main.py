import serial
from ssi_barcode import ssi


with serial.Serial('/dev/ttyACM0', 9600, rtscts=True) as ser:
    #START_SESSION = b'\x04\xe4\x04\x00'
    #START_SESSION_CSUM = csum(START_SESSION)
    #ser.write(START_SESSION + START_SESSION_CSUM)
    t = ssi.SSITransport(ser)
    t.run()
