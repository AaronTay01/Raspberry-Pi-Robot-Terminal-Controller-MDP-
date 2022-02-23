import os, sys
import serial
import time
from setting import *


class STMRobot:
	def __init__(self):
		self.port = "/dev/ttyUSB1"
		self.baudRate = STM_BAUDRATE
		self.ser = None
		self.isConnected = False
		self.threadListening = False

	def connectToSTM(self):
		time.sleep(1)
		print("Connecting to STM")
		try:
			self.ser = serial.Serial(SERIAL_PORT0, self.baudRate, timeout=3)
			print("Serial Port 0 Connected to STM")
			self.isConnected = True
		except:
			try:
				self.ser = serial.Serial(SERIAL_PORT1, self.baudRate, timeout=3)
				print("Serial Port 1 Connected to STM")
				self.isConnected = True
			except Exception as e:
				print("No Connection is found... %s" % str(e))
				self.isConnected = False
				self.threadListening = False
				try:
					self.ser.close()
				except:
					print()

	def disconnectFromSTM(self):
		self.ser.close()
		self.isConnected = False
		self.threadListening = False
		print("Disconnected from STM.")

	def writeToSTM(self, msg):
		try:
			self.ser.write(str.encode(msg))
			print("Sent to STM: %s" % msg)
		except OSError as e:
			print(e)
			self.disconnectFromSTM()
		except Exception as e:
			print("Failed to send message to STM. Exception Error : %s" % str(e))
			self.disconnectFromSTM()

	def readFromSTM(self):
		self.threadListening = True
		try:
			print("Run Read STM")
			msg = self.ser.readline()
			#print("msg: ", str(msg))
			receivedMsg = msg.decode('utf-8')
			receivedMsg = str(receivedMsg)
			print("Received from STM: %s" % receivedMsg)
			return receivedMsg
		except Exception as e:
			print("Failed to receive message from STM", str(e))
			self.disconnectFromSTM()
