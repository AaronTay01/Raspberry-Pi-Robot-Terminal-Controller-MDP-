from unittest.main import main
import uuid
import bluetooth
from bluetooth import *
from setting import *
import time
import socket

#BLUETOOTH_PORT = 0 #some number 

class AndroidApplication(object):

	def __init__(self):
		#self.serverSocket = None
		self.sock = None
		self.isConnected = False
		self.threadListening = False

	def connectToAndroid (self):
		try:
			# #Server
			# server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
			# server_sock.bind(("", BLUETOOTH_PORT))
			# server_sock.listen(1)

			# port = server_sock.getsockname()[1]
			# bluetooth.advertise_service(server_sock, "SampleServer", service_id=uuid,
			# 							service_classes=[UUID, bluetooth.SERIAL_PORT_CLASS],
			# 							profiles=[bluetooth.SERIAL_PORT_PROFILE],
			# 							# protocols=[bluetooth.OBEX_UUID]
			# 							)

			# print("Waiting for connection on RFCOMM channel", port)

			# client_sock, client_info = server_sock.accept()
			# print("Accepted connection from", client_info)

			self.sock = BluetoothSocket(RFCOMM)
			if self.isConnected is False:
				print("Connecting to Android Device")
				service_matches = find_service( uuid = UUID, address = ANDROID_ADDR )
				if  len(service_matches) > 0:	
					first_match = service_matches[0]
					port = first_match["port"]
					host = first_match["host"]
					#print(service_matches)
					#print(service_matches[0])

					
					self.sock.connect((host, port))
					print ("Successfully Connected to Android :)")
					print ("Connection via Bluetooth port: %s, host: %s" %(port, host))
					self.isConnected = True
					self.threadListening = False
				else:
					print("Cannot find bluetooth device")
					#self.sock.close()
					self.isConnected = False
					self.threadListening = False
					time.sleep(2)
		except Exception as e:
			print ("Bluetooth connection has failed, waiting to reconnect. ", str(e))
			self.sock.close()
			print ("Closing bluetooth connection")
			self.isConnected = False
			self.threadListening = False

	def disconnectFromAndroid (self):
		try:
			self.sock.close()
			print ("Closing bluetooth (client)")
			self.threadListening = False
			self.isConnected = False
		except Exception as e:
			print("Failed to disconnect from Android: %s" %str(e))

	def writeToAndroid (self, msg):
		try:
			self.sock.send(msg)
			print ("Sent to Android : %s" %(msg))
		except Exception as e:
			print("Error with Bluetooth(write): ", str(e))
			self.isConnected = False 
			self.sock.close()
			self.connectToAndroid()

	def readFromAndroid (self):
		self.threadListening = True
		try:
			msg = self.sock.recv(1024)
			msg = msg.decode('utf-8')
			return msg
		except Exception as e:
			print("Error with Bluetooth(read): ", str(e))
			self.threadListening = False
			self.isConnected = False
			return
