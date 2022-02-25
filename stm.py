import serial
import time
from setting import *


class STMRobot:
	def __init__(self):
		self.ser = None

		self.isConnected = False
		self.threadListening = False

	def connectToSTM(self):
		try:
			self.ser = serial.Serial(SERIAL_PORT0, STM_BAUDRATE)
			print("Connected to STM")
			self.isConnected = True
		except Exception as e:
			print("No Connection is found... %s" % str(e))
			self.isConnected = False
			self.threadListening = False
			if self.ser:
				self.ser.close()
			time.sleep(1)


	'''def connectToSTM2(self):
		time.sleep(1)
		print("Connecting to STM")
		if self.ser:
			self.ser.close()
		try:
			self.ser = serial.Serial(SERIAL_PORT0, self.baudRate, timeout=3)
			print("Serial Port 0 Connected to STM")
			self.isConnected = True
		except:
			self.ser.close()
			try:
				time.sleep(1)
				self.ser = serial.Serial(SERIAL_PORT1, self.baudRate, timeout=3)
				print("Serial Port 1 Connected to STM")
				self.isConnected = True
			except Exception as e:
				print("No Connection is found... %s" % str(e))
				self.isConnected = False
				self.threadListening = False
				if self.ser:
					self.ser.close()'''


	def disconnectFromSTM(self):
		try:
			self.ser.close()
			self.isConnected = False
			self.threadListening = False
			print("Disconnected from STM.")
		except Exception as error:
			print("Error Disconnecting: ", str(error))

	def writeToSTM(self, msg):
		try:
			# self.ser.write(str.encode(msg))
			self.ser.write(msg.encode("utf-8"))
			print("Sent to STM: %s" % msg)
		except OSError as e:
			print(e)
			self.disconnectFromSTM()
		except Exception as e:
			self.disconnectFromSTM()
			print("Failed to send message to STM. Exception Error : %s" % str(e))

	def readFromSTM(self):
		try:
			# msg = self.ser.readline().lstrip(b"\x00")
			msg = self.ser.readline()
			print("Byte msg: ", msg)
			msg = msg.lstrip(b"\x00")
			#	msg = msg.lstrip(b"\x00").decode("utf-8")
			msg = msg.decode("utf-8").strip()
			# receivedMsg = msg.decode('utf-8')
			# receivedMsg = str(receivedMsg).strip()
			# print("Received from STM: %s" % msg)
			return msg
		except Exception as e:
			self.disconnectFromSTM()
			print("Failed to receive message from STM", str(e))
