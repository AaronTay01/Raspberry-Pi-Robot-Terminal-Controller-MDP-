#from operator import truediv
#from tkinter import E
from stm import *
from android import *
from pc import *
import threading
import os
from utils import format_for
from multiprocessing import Process, Queue

#import argparse
#import cv2
import numpy as np
#import sys
import time
#import serial
from threading import Thread
#import importlib.util


class RaspberryPi(threading.Thread):
	def __init__(self):
		self.STMThread = STMRobot()
		self.pcThread = PCInterface()
		self.androidThread = AndroidApplication()

		#initalise connections
		#self.STMThread.connectToSTM()
		self.androidThread.connectToAndroid()
		self.pcThread.connectToPC()

		self.msg_queue = Queue()
		time.sleep(1)


	def multithread(self):
		#Android read and write thread
		readAndroidThread = threading.Thread(target = self.readFromAndroid, args = (), name = "read_android_thread")
		writeAndroidThread = threading.Thread(target = self.writeToAndroid, args = (), name = "write_android_thread")

		"""# STM read and write thread
		readSTMThread = threading.Thread(target = self.read_STM, args = (), name = "read_STM_thread")
		writeSTMThread = threading.Thread(target = self.write_STM, args = (), name = "write_STM_thread")"""

		# PC read and write thread
		readPCthread = threading.Thread(target = self.readFromPC, args = (), name = "read_pc_thread")
		writePCthread = threading.Thread(target = self.writeToPC, args = (), name = "write_pc_thread")

		# Set daemon for all thread      
		readPCthread.daemon = True
		writePCthread.daemon = True

		readAndroidThread.daemon = True
		writeAndroidThread.daemon = True

		#readSTMThread.daemon = True
		#writeSTMThread.daemon = True

		# start running the thread for PC
		readPCthread.start()

		# Start running thread for Android
		readAndroidThread.start()
 
		# Start running thread for STM
		#readSTMThread.start()

	def disconnectAll(self):
		self.STMThread.disconnectFromSTM()
		self.androidThread.disconnectFromAndroid()
		self.pcThread.disconnectFromPC()

	def writeToAndroid(self, message):
		if self.androidThread.isConnected and message is not None:
			self.androidThread.writeToAndroid(message)

	def readFromAndroid(self):
		while True:
			androidMessage = self.androidThread.readFromAndroid()
			if androidMessage is not None:
				print("Read From Android: ", str(androidMessage))
		
	def readFromPC(self, msg_queue):
			while True:
				pcMessage = self.pcThread.readFromPC()
				if pcMessage is not None:
					if pcMessage['target'] == 'ST':
						msg_queue.put_nowait(format_for('AND', pcMessage['Payload']))
						#send ready signal to Android
				print("Read from PC: ", str(pcMessage))



	def writeToPC(self, message):
		if self.pcThread.isConnected and message is not None:
			self.pcThread.writeToPC(message)

	def writeToSTM (self, message):
		if (self.STMThread.isConnected and message):
			self.STMThread.writeToSTM(message)
			return True
		return False
	def readFromSTM (self):
		while True:
			serialmsg = self.STMThread.readFromSTM()
			if serialmsg is not None:
				print("Read from STM: ", str(serialmsg))
				#msg_remove = serialmsg.replace('@','')
				#new_msg = msg_remove.split(",")

				#serialmsgArray = new_msg[0].split(":")
				#header = serialmsgArray[0]

if __name__ == "__main__":
	print("Program Starting")
	main = RaspberryPi()

	try:
		main.multithread()
		print("Starting MultiTreading")

		try:
			print("send message")
			count = 0
			while True:
				count+=1
				#main.writeToPC("RPI Message " + str(count))
				time.sleep(3)
				#main.writeToSTM("RPI Message")
				main.writeToAndroid("RPI Message " + str(count))
		except Exception as e:
			print("Main program: ", str(e))

	except Exception as e:
		print(str(e))
		#main.disconnectAll()
	except KeyboardInterrupt as e:
		print("Terminating program")
		#main.disconnectAll()
		print("Program Terminated")
