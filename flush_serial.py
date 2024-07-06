import serial




with serial.Serial('/dev/ttyACM0', 9600, rtscts=True) as ser:
    while True:
        data = ser.read(1)
        print(data.hex())

