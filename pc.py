import json
import socket
import sys
import traceback
import errno
from setting import *
import time

""""
Client
# Connect a client socket to my_server:8000 (change my_server to the
# hostname of your server)
client_socket = socket.socket()
client_socket.connect(('192.168.38.21', 8000))

# Make a file-like object out of the connection
connection = client_socket.makefile('wb')         
"""
class PCInterface(object):

	def __init__(self):
		self.host = RPI_WIFI_IP
		self.port = WIFI_PORT
		self.isConnected = False
		self.connection = None
		self.address = None
		self.threadListening = False




	def connectToPC (self):
		try:
			self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			#wifi change to self.host
			self.socket.bind(('192.168.38.1', self.port))

			self.socket.listen(3)
			print ("Waiting for connection from PC........")

			# Accept a single connection
			self.connection, self.address = self.socket.accept()
			print ("Connected to PC with the IP Address: ", str(self.address), ":)")
			self.isConnected = True

		except Exception as e:
			print ("Connecting to PC Error : %s" % str(e))
			self.isConnected = False
			self.threadListening = False
			self.socket.close()


	def disconnectFromPC(self):
		try:
			self.socket.close()
			self.connected = False
			#self.threadListening = False
			print("Disconnected from PC successfully.")
		except Exception as e:
			print("Failed to disconnect from PC: %s" %str(e))

	def writeToPC(self, message):
		try:
			encoded_string = message.encode()
			byte_array = bytearray(encoded_string)
			self.connection.send(byte_array)
			#self.connection.sendto(bytes(message + '\n'), self.address)
			print("Send to PC: " , message)
		except Exception as e:
			print("Cannot Write to PC ", str(e))
			self.isConnected = False
			self.connection.close()

	def readFromPC (self):
		self.threadListening = True
		try:
			message = self.connection.recv(1024)
			msg = message.decode()
			return msg
				
		except Exception as e:
			print ('PC message reading failed. Exception Error : %s' % str(e))
			self.threadListening = False
			self.isConnected = False
			return


		