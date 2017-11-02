# Copyright (c) 2017 Adafruit Industries
# Author: Dean Miller
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import logging
from Adafruit_bitfield import Adafruit_bitfield
import time

SEESAW_STATUS_BASE = 0x00
SEESAW_GPIO_BASE = 0x01
SEESAW_SERCOM0_BASE = 0x02

SEESAW_TIMER_BASE = 0x08
SEESAW_ADC_BASE = 0x09
SEESAW_DAC_BASE = 0x0A
SEESAW_INTERRUPT_BASE = 0x0B
SEESAW_DAP_BASE = 0x0C
SEESAW_EEPROM_BASE = 0x0D
SEESAW_NEOPIXEL_BASE = 0x0E

SEESAW_GPIO_DIRSET_BULK = 0x02
SEESAW_GPIO_DIRCLR_BULK = 0x03
SEESAW_GPIO_BULK = 0x04
SEESAW_GPIO_BULK_SET = 0x05
SEESAW_GPIO_BULK_CLR = 0x06
SEESAW_GPIO_BULK_TOGGLE = 0x07
SEESAW_GPIO_INTENSET = 0x08
SEESAW_GPIO_INTENCLR = 0x09
SEESAW_GPIO_INTFLAG = 0x0A
SEESAW_GPIO_PULLENSET = 0x0B
SEESAW_GPIO_PULLENCLR = 0x0C

SEESAW_STATUS_HW_ID = 0x01
SEESAW_STATUS_VERSION = 0x02
SEESAW_STATUS_OPTIONS = 0x03
SEESAW_STATUS_SWRST = 0x7F

SEESAW_TIMER_STATUS = 0x00
SEESAW_TIMER_PWM = 0x01

SEESAW_ADC_STATUS = 0x00
SEESAW_ADC_INTEN = 0x02
SEESAW_ADC_INTENCLR = 0x03
SEESAW_ADC_WINMODE = 0x04
SEESAW_ADC_WINTHRESH = 0x05
SEESAW_ADC_CHANNEL_OFFSET = 0x07

SEESAW_SERCOM_STATUS = 0x00
SEESAW_SERCOM_INTEN = 0x02
SEESAW_SERCOM_INTENCLR = 0x03
SEESAW_SERCOM_BAUD = 0x04
SEESAW_SERCOM_DATA = 0x05

SEESAW_NEOPIXEL_STATUS = 0x00
SEESAW_NEOPIXEL_PIN = 0x01
SEESAW_NEOPIXEL_SPEED = 0x02
SEESAW_NEOPIXEL_BUF_LENGTH = 0x03
SEESAW_NEOPIXEL_BUF = 0x04
SEESAW_NEOPIXEL_SHOW = 0x05

ADC_INPUT_0_PIN = 0x02
ADC_INPUT_1_PIN  = 0x03
ADC_INPUT_2_PIN = 0x04
ADC_INPUT_3_PIN = 0x05

PWM_0_PIN = 0x04
PWM_1_PIN = 0x05
PWM_2_PIN = 0x06
PWM_3_PIN = 0x07

class Seesaw(object):

	INPUT = 0x00
	OUTPUT = 0x01
	INPUT_PULLUP = 0x02

	def __init__(self, addr=0x49, i2c=None, **kwargs):
		# Create I2C device.
		if i2c is None:
			import Adafruit_GPIO.I2C as I2C
			i2c = I2C
		self._bus = i2c.get_i2c_device(addr, **kwargs)._bus
		self.addr = addr

		self._sercom_status = Adafruit_bitfield([('ERROR', 1), ('DATA_RDY', 1)])
		self._sercom_inten = Adafruit_bitfield([('ERROR', 1), ('DATA_RDY', 1)])
		self.begin()


	## \brief      Start the seesaw
	#
	#				This should be called when your sketch is connecting to the seesaw
	# 
	#  \param      addr the I2C address of the seesaw
	#
	#  \return     true if we could connect to the seesaw, false otherwise

	def begin(self):
		self.sw_reset()
		time.sleep(.500)

		c = self.read8(SEESAW_STATUS_BASE, SEESAW_STATUS_HW_ID)

		if c != 0x55:
			print(c)
			raise RuntimeError("Seesaw hardware ID returned is not correct! Please check your wiring.")


	## \brief     perform a software reset. This resets all seesaw registers to their default values.
	#
	#  			This is called automatically from Adafruit_seesaw.begin()
	# 
	#
	#  \return     none

	def sw_reset(self):

		self.write8(SEESAW_STATUS_BASE, SEESAW_STATUS_SWRST, 0xFF)


	## \brief     Returns the available options compiled into the seesaw firmware.
	# 
	#
	#  \return     the available options compiled into the seesaw firmware. If the option is included, the
	#				corresponding bit is set. For example, 
	#				if the ADC module is compiled in then (ss.getOptions() & (1UL << SEESAW_ADC_BASE)) > 0

	def get_options(self):

		buf = self.read(SEESAW_STATUS_BASE, SEESAW_STATUS_OPTIONS, 4)
		ret = (buf[0] << 24) | (buf[1] << 16) | (buf[2] << 8) | buf[3]
		return ret


	## \brief     Returns the version of the seesaw
	#
	#  \return     The version code. Bits [31:16] will be a date code, [15:0] will be the product id.

	def get_version(self):

		buf = self.read(SEESAW_STATUS_BASE, SEESAW_STATUS_VERSION, 4)
		ret = (buf[0] << 24) | (buf[1] << 16) | (buf[2] << 8) | buf[3]
		return ret


	## \brief     Set the mode of a GPIO pin.
	# 
	#  \param      pin the pin number. On the SAMD09 breakout, this corresponds to the number on the silkscreen.
	#  \param		mode the mode to set the pin. One of Seesaw.INPUT, Seesaw.OUTPUT, or Seesaw.INPUT_PULLUP.
	#
	#  \return     none

	def pin_mode(self, pin,  mode):

		self.pin_mode_bulk(1 << pin, mode)



	## \brief     Set the output of a GPIO pin
	# 
	#  \param      pin the pin number. On the SAMD09 breakout, this corresponds to the number on the silkscreen.
	#	\param		value the value to write to the GPIO pin. This should be True or False.
	#
	#  \return     none

	def digital_write(self, pin,  value):

		self.digital_write_bulk(1 << pin, value)



	## \brief     Read the current status of a GPIO pin
	# 
	#  \param      pin the pin number. On the SAMD09 breakout, this corresponds to the number on the silkscreen.
	#
	#  \return     the status of the pin. HIGH or LOW (1 or 0).

	def digital_read(self, pin):

		return self.digital_read_bulk((1 << pin)) != 0


	## \brief     read the status of multiple pins.
	# 
	#  \param      pins a bitmask of the pins to write. On the SAMD09 breakout, this corresponds to the number on the silkscreen.
	#				For example, passing 0b0110 will return the values of pins 2 and 3.
	#
	#  \return     the status of the passed pins. If 0b0110 was passed and pin 2 is high and pin 3 is low, 0b0010 (decimal number 2) will be returned.

	def digital_read_bulk(self, pins):

		buf = self.read(SEESAW_GPIO_BASE, SEESAW_GPIO_BULK, 4)
		ret = ( (buf[0] & 0xF) << 24) | (buf[1] << 16) | (buf[2] << 8) | buf[3] #TODO: weird overflow error, fix
		return ret & pins


	## \brief     Enable or disable GPIO interrupts on the passed pins
	# 
	#  \param      pins a bitmask of the pins to write. On the SAMD09 breakout, this corresponds to the number on the silkscreen.
	#				For example, passing 0b0110 will enable or disable interrups on pins 2 and 3.
	#	\param		enabled pass true to enable the interrupts on the passed pins, false to disable the interrupts on the passed pins.
	#
	#  \return     none

	def set_GPIO_interrupts(self, pins, enabled):

		cmd =  bytearray([(pins >> 24) & 0xFF, (pins >> 16) & 0xFF, (pins >> 8) & 0xFF, pins & 0xFF])
		if enabled:
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_INTENSET, cmd)
		else:
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_INTENCLR, cmd)


	## \brief     read the analog value on an ADC-enabled pin.
	# 
	#  \param      pin the number of the pin to read. On the SAMD09 breakout, this corresponds to the number on the silkscreen.
	#				On the default seesaw firmware on the SAMD09 breakout, pins 2, 3, and 4 are ADC-enabled.
	#
	#  \return     the analog value. This is an integer between 0 and 1023

	def analog_read(self, pin):

		if pin == ADC_INPUT_0_PIN:
			p = 0
		elif pin == ADC_INPUT_1_PIN:
			p = 1
		elif pin == ADC_INPUT_2_PIN: 
			p = 2
		elif pin == ADC_INPUT_3_PIN: 
			p = 3
		else:
			return 0

		buf = self.read(SEESAW_ADC_BASE, SEESAW_ADC_CHANNEL_OFFSET + p, 2)
		ret = buf[0] << 8 | buf[1]
		time.sleep(.001)
		return ret



	## \brief     set the mode of multiple GPIO pins at once.
	# 
	#  \param      pins a bitmask of the pins to write. On the SAMD09 breakout, this corresponds to the number on the silkscreen.
	#				For example, passing 0b0110 will set the mode of pins 2 and 3.
	#	\param		mode the mode to set the pins to. One of Seesaw.INPUT, Seesaw.OUTPUT, or Seesaw.INPUT_PULLUP.
	#
	#  \return     none

	def pin_mode_bulk(self, pins, mode):

		cmd =  bytearray([(pins >> 24) & 0xFF, (pins >> 16) & 0xFF, (pins >> 8) & 0xFF, pins & 0xFF ])

		if mode == self.OUTPUT:
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_DIRSET_BULK, cmd)
			
		elif mode == self.INPUT:
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_DIRCLR_BULK, cmd)
			
		elif mode == self.INPUT_PULLUP:
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_DIRCLR_BULK, cmd)
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_PULLENSET, cmd)
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_BULK_SET, cmd)
			


	## \brief     write a value to multiple GPIO pins at once.
	# 
	#  \param      pins a bitmask of the pins to write. On the SAMD09 breakout, this corresponds to the number on the silkscreen.
	#				For example, passing 0b0110 will write the passed value to pins 2 and 3.
	#	\param		value pass True to set the output on the passed pins high, False to set the output on the passed pins low.
	#
	#  \return     none

	def digital_write_bulk(self, pins, value):

		cmd =  bytearray([(pins >> 24) & 0xFF, (pins >> 16) & 0xFF, (pins >> 8) & 0xFF, pins & 0xFF])
		if value:
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_BULK_SET, cmd)
		else:
			self.write(SEESAW_GPIO_BASE, SEESAW_GPIO_BULK_CLR, cmd)



	## \brief     write a PWM value to a PWM-enabled pin
	# 
	#  \param      pin the number of the pin to write. On the SAMD09 breakout, this corresponds to the number on the silkscreen.
	#				on the default seesaw firmware on the SAMD09 breakout, pins 5, 6, and 7 are PWM enabled.
	#	\param		value a number between 0 and 255 to write to the pin.
	#
	#  \return     none

	def analog_write(self, pin, value):

		p = -1
		if pin == PWM_0_PIN:
			p = 0 
		elif pin == PWM_1_PIN:
			p = 1 
		elif pin == PWM_2_PIN:
			p = 2 
		elif pin == PWM_3_PIN:
			p = 3

		if p > -1:
			cmd = bytearray([p, value])
			self.write(SEESAW_TIMER_BASE, SEESAW_TIMER_PWM, cmd)


	## \brief     Enable the data ready interrupt on the passed sercom. Note that both the interrupt module and
	#				the passed sercom must be compiled into the seesaw firmware for this to function.
	#				If both of these things are true, the interrupt pin on the seesaw will fire when
	#				there is data to be read from the passed sercom. On the default seesaw firmeare
	#				on the SAMD09 breakout, no sercoms are enabled.
	# 
	#  \param      sercom the sercom to enable the interrupt on. 
	#
	#  \return     none

	def enable_sercom_data_rdy_interrupt(self, sercom):

		self._sercom_inten.DATA_RDY = 1
		self.write8(SEESAW_SERCOM0_BASE + sercom, SEESAW_SERCOM_INTEN, _sercom_inten.get())


	## \brief     Disable the data ready interrupt on the passed sercom.
	# 
	#  \param      sercom the sercom to disable the interrupt on. 
	#
	#  \return     none

	def disable_sercom_data_rdy_interrupt(self, sercom):

		_sercom_inten.DATA_RDY = 0
		self.write8(SEESAW_SERCOM0_BASE + sercom, SEESAW_SERCOM_INTEN, _sercom_inten.get())



	## \brief     Reads a character from the passed sercom if one is available. Note that on
	#				the default seesaw firmware on the SAMD09 breakout no sercoms are enabled.
	# 
	#  \param      sercom the sercom to read data from.
	#
	#  \return     a character read from the sercom.

	def read_sercom_data(self, sercom):

		return self.read8(SEESAW_SERCOM0_BASE + sercom, SEESAW_SERCOM_DATA)


	## \brief     Set the seesaw I2C address. This will automatically call Adafruit_seesaw.begin()
	#				with the new address.
	# 
	#  \param      addr the new address for the seesaw. This must be a valid 7 bit I2C address.
	#
	#  \return     none

	def set_i2c_addr(self, addr):

		self.eeprom_write8(SEESAW_EEPROM_I2C_ADDR, addr)
		time.sleep(.250)
		self.begin(addr) #restart w/ the new addr


	## \brief     Read the I2C address of the seesaw
	#
	#  \return     the 7 bit I2C address of the seesaw... which you probably already know because you
	#				just read data from it.

	def get_i2c_addr(self,):

		return self.read8(SEESAW_EEPROM_BASE, SEESAW_EEPROM_I2C_ADDR)


	## \brief     Write a 1 byte to an EEPROM address
	# 
	#  \param      addr the address to write to. On the default seesaw firmware on the SAMD09
	#				breakout this is between 0 and 63.
	#	\param		val to write between 0 and 255
	#
	#  \return     none

	def eeprom_write8(self, addr,  val):
		self.eeprom_write(addr, bytearray([val]))



	## \brief     write a string of bytes to EEPROM starting at the passed address
	# 
	#  \param      addr the starting address to write the first byte. This will be automatically
	#				incremented with each byte written.
	#	\param		buf the buffer of bytes to be written.
	#
	#  \return     none

	def eeprom_write(self, addr,  buf):

		self.write(SEESAW_EEPROM_BASE, addr, buf)



	## \brief     Read 1 byte from the specified EEPROM address.
	# 
	#  \param      addr the address to read from. One the default seesaw firmware on the SAMD09
	#				breakout this is between 0 and 63.
	#
	#  \return     the value between 0 and 255 that was read from the passed address.

	def eeprom_read8(self, addr):

		return self.read8(SEESAW_EEPROM_BASE, addr)


	## \brief     Set the baud rate on SERCOM0.
	# 
	#  \param      baud the baud rate to set. This is an integer value. Baud rates up to 115200 are supported.
	#
	#  \return     none

	def uart_set_baud(self, baud):

		cmd = bytearray([(baud >> 24) & 0xFF, (baud >> 16) & 0xFF, (baud >> 8) & 0xFF, baud & 0xFF])
		self.write(SEESAW_SERCOM0_BASE, SEESAW_SERCOM_BAUD, cmd)



	## \brief     Write 1 byte to the specified seesaw register.
	# 
	#  \param      regHigh the module address register (ex. SEESAW_NEOPIXEL_BASE)
	#	\param		regLow the function address register (ex. SEESAW_NEOPIXEL_PIN)
	#	\param		value the value between 0 and 255 to write
	#
	#  \return     none

	def write8(self, regHigh, regLow, value):

		self.write(regHigh, regLow, bytearray([value]))


	## \brief     read 1 byte from the specified seesaw register.
	# 
	#  \param      regHigh the module address register (ex. SEESAW_STATUS_BASE)
	#	\param		regLow the function address register (ex. SEESAW_STATUS_VERSION)
	#
	#  \return     the value between 0 and 255 read from the passed register

	def read8(self, regHigh, regLow):

		ret = self.read(regHigh, regLow, 1)

		return ret[0]


	## \brief     Read a specified number of bytes from the seesaw.
	# 
	#  \param      regHigh the module address register (ex. SEESAW_STATUS_BASE)
	#	\param		regLow the function address register (ex. SEESAW_STATUS_VERSION)
	#	\param		num the number of bytes to read.
	#	\param		delay an optional delay (seconds) in between setting the read register and reading
	#				out the data. This is required for some seesaw functions (ex. reading ADC data)
	#
	#  \return     the buffer of bytes read

	def read(self, regHigh,  regLow, length, delay=.001):
		self.write(regHigh, regLow)

		time.sleep(delay)

		ret = self._bus._device.read(length)
		return [ord(x) for x in ret]


	## \brief     Write a specified number of bytes to the seesaw from the passed buffer.
	# 
	#  \param      regHigh the module address register (ex. SEESAW_GPIO_BASE)
	#	\param		regLow the function address register (ex. SEESAW_GPIO_BULK_SET)
	#	\param		buf the buffer the the bytes from
	#
	#  \return     none

	def write(self, regHigh,  regLow, buf = None):
		c = bytearray([regHigh, regLow])
		if not buf == None:
			c = c + buf

		self._bus._select_device(self.addr)
		self._bus._device.write(c)