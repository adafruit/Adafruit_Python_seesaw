from Adafruit_Seesaw import Seesaw
import time

ss = Seesaw()

ss.pin_mode(15, ss.OUTPUT)

while True:
        ss.digital_write(15, True) #turn LED on
        time.sleep(1)
        ss.digital_write(15, False) #turn LED off
        time.sleep(1)
