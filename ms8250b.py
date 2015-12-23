#!/usr/bin/python3

import serial
import struct
import array
import threading
import time
import sys
import copy

#  1111
# 6    2
# 6    2
#  7777
# 5    3
# 5    3
#  4444        
# 
#   
num_dict = {0: ' ', 0x68: 'L', 0x7D: 0, 0x05: 1,0x5B: 2,0x1F: 3,0x27: 4,0x3E: 5,0x7E: 6,0x15: 7,0x7F: 8,0x3F: 9}

def setbit(value, nbit):
	return value | (1 << nbit)

def decode_digit(byte1, byte2):
	val = ((byte1 & 7) << 4) + byte2
	if val in num_dict.keys():
		val = num_dict[val]
	else:
		val = None
	point = byte1 & 8 
	if point == 8:
		point = 1
	else:
		point = 0
	return val, point

def data2hex(data):
	line = ""
	for b in data:
		line += "%X " % b
	line = line[:-1]
	return line

class Multimeter:
	def __init__(self, port=None):
		self.thread = threading.Thread()
		if port == None:
			raise Exception("Serial port not specified")
		self.port_name = port
		self.port = serial.Serial(port, 2400)
		self.neval = 0
		self.segments = array.array('B', [0]*14)
		self.thread.run = self.run
		self.thread.start()
		self.stop_flag = False
		self.reading = {}
		self.valock = threading.Lock()

	def run(self):
		for i in range(0,28):
			while 1:
				try:
					one_byte = self.port.read(1)
					break
				except:
					pass
				
			num = struct.unpack("B", one_byte)[0]
			seg = ((0xF0 & num) >> 4) - 1
			if seg == 14:
				break
		while 1:
			if self.stop_flag:
				break
			data = self.port.read(14)
			decoded = self.decode_data(data)

	def stop(self):
		self.stop_flag = True
		self.thread.join()

	def decode_data(self, data):
		retval = {}
		data_values = array.array('B', list(map(lambda x: x & 0x0F, data)))
		digit1 = decode_digit(data_values[1], data_values[2])
		digit2 = decode_digit(data_values[3], data_values[4])
		digit3 = decode_digit(data_values[5], data_values[6])
		digit4 = decode_digit(data_values[7], data_values[8])
		sig = lambda x: "-" if x[1] == 1 else ""
		pnt = lambda x: "." if x[1] == 1 else ""
		digit_str = sig(digit1) + str(digit1[0]) + pnt(digit2) + \
			str(digit2[0]) + pnt(digit3)+ str(digit3[0]) + pnt(digit4) + \
			str(digit4[0])

		if isinstance(digit1[0], int) and isinstance(digit2[0], int) and \
			isinstance(digit3[0], int) and isinstance(digit1[0], int):
			measured_value = float(digit_str)
		else:
			measured_value = digit_str

		if data_values[9] == 2:
			mult = 1000.0
		elif data_values[9] == 4:
			mult = 1e-9
		elif data_values[9] == 8:
			mult = 1e-6
		elif data_values[10] == 2:
			mult = 1000000
		elif data_values[10] == 8:
			mult = 1e-3
		else:
			mult = 1

		mtype = ''
		if data_values[11] == 4:
			mtype = "Ohm"
		elif data_values[11] == 8:
			mtype = "F"
		elif data_values[12] == 2:
			mtype = "Hz"
		elif data_values[12] == 4:
			mtype = "V"
		elif data_values[12] == 8:
			mtype = "A"

		if (isinstance(measured_value, float)):
			measured_value *= mult

		self.valock.acquire()
		self.reading["value"] = measured_value
		self.reading["type"] = mtype
		self.valock.release()

	def getValue(self):
		self.valock.acquire()
		value = copy.deepcopy(self.reading)
		self.valock.release()
		return value


	def __del__(self):
		self.port.close()




