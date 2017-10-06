from Adafruit_Seesaw import Seesaw
import time

BUTTON_RIGHT = 6
BUTTON_DOWN  = 7
BUTTON_LEFT  = 9
BUTTON_UP    = 10
BUTTON_SEL   = 14
button_mask =  (1 << BUTTON_RIGHT) | (1 << BUTTON_DOWN) | (1 << BUTTON_LEFT) | (1 << BUTTON_UP) | (1 << BUTTON_SEL) 

ss = Seesaw()

ss.pin_mode_bulk(button_mask, ss.INPUT_PULLUP);

last_x = 0
lasy_y = 0

while True:
	x = ss.analog_read(2)
	y = ss.analog_read(3)
	  
	if  (abs(x - last_x) > 3) or (abs(y - last_y) > 3):
		print(x, y)
		last_x = x
		last_y = y

	buttons = ss.digital_read_bulk(button_mask)
	if not (buttons & (1 << BUTTON_RIGHT)):
		print("Button A pressed")

	if not (buttons & (1 << BUTTON_DOWN)):
		print("Button B pressed")

	if not (buttons & (1 << BUTTON_LEFT)):
		print("Button Y pressed")

	if not (buttons & (1 << BUTTON_UP)):
		print("Button x pressed")

	if not (buttons & (1 << BUTTON_SEL)):
		print("Button SEL pressed")

	time.sleep(.01)