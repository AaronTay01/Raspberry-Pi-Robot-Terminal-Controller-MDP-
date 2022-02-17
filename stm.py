import os, sys
import serial
import time
from setting import *


class STMRobot:
	def __init__(self):
		self.port = "/dev/ttyUSB1"
		self.baudRate = STM_BAUDRATE
		self.ser = 0
		self.isConnected = False
		self.threadListening = False

	def connectToSTM(self):
		time.sleep(1)
		print("Connecting to STM")
		try:
			self.ser = serial.Serial(SERIAL_PORT0, self.baudRate, timeout=3)
			print ("Serial Port 0 Connected to STM")
			self.isConnected = True
		except:
			try:
				self.ser = serial.Serial(SERIAL_PORT1, self.baudRate, timeout=3)
				print("Serial Port 1 Connected to STM")
				self.isConnected = True
			except Exception as e:
				print("No Connection is found... %s" %str(e))
				self.isConnected = False

	def disconnectFromSTM (self):
		self.ser.close()
		self.isConnected = False
		print("Disconnected from STM.")

	def writeToSTM (self, msg):
		try:
			self.ser.write(str.encode(msg))
			print ("Sent to STM: %s" % msg)
		
		except Exception as e:
			print ("Failed to send message to STM. Exception Error : %s" %str(e))
			self.isConnected = False
			self.connectToSTM()

	def readFromSTM (self):
		self.threadListening = True
		while True:
			try:
				msg = self.ser.readline()
				receivedMsg = msg.decode('utf-8')
				receivedMsg = str(receivedMsg)
				print ("Received from STM: %s" % receivedMsg)
				return receivedMsg
			except Exception as e:
				print ("Failed to receive message from STM")
				break
		self.isConnected = False
		self.threadListening = False
