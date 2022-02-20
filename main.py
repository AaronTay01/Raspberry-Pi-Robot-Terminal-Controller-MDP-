#from operator import truediv
#from tkinter import E
import string
from stm import *
from android import *
from pc import *
import threading
import os
from utils import format_for
from multiprocessing import Process, Queue
from picamera import PiCamera

#import argparse
#import cv2
import numpy as np
#import sys
import time
#import serial
from threading import Thread
#import importlib.util

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096 # send 4096 bytes each time step

class RaspberryPi(threading.Thread):
	def __init__(self):
		self.STMThread = STMRobot()
		self.pcThread = PCInterface()
		self.androidThread = AndroidApplication()

		#True if there is algorithm path in the textFile
		self.pathReady = False

		#True if everything is ready to Start
		self.primed = False

		#check if path is being deployed
		self.pathDeployed = False

		#number of paths
		self.path_data = []

		#initalize Queue
		self.path_queue = Queue()
		#self.manual_queue = Queue()
		self.android_queue = Queue()
		self.rpi_queue = Queue()

		#run command thread
		threading.Thread(target=self.command_forwarder).start()

		#get algo path from txt file
		coursePath = self.readTxtFile()

		#insert algo path to queue
		self.pathReady = self.insertPath(coursePath)

		#serial Received Message
		self.serialMsg = None
		
	#print algo path from queue (Only for testing)
	def printPath(self):
		while True:
			if not self.path_queue.empty():
				msg = self.path_queue.get()
				print(msg)
			else:
				break

	#insert path from textfile onto queue
	def insertPath(self, coursePath):
		coursePath = self.readTxtFile()
		for i in coursePath:
			#print(i)
			self.path_queue.put(i)
		#check list is not empty
		if coursePath:
			return True
		else:
			return False
		#self.printPath()

	#threading
	def run(self):
		# Android control loop
		if self.androidThread.isConnected == False:
				self.androidThread.connectToAndroid()
		elif self.androidThread.isConnected == True:
			if self.androidThread.threadListening == False:
				try:
					threading.Thread(target=self.readFromAndroid).start() # start Android socket listener thread
				except Exception as e:
					print("Android threading error: %s" %str(e))
					self.androidThread.isConnected = False
		# STM control loop
		if self.STMThread.isConnected == False:
			self.STMThread.connectToSTM()
		elif self.STMThread.isConnected == True:
			if self.STMThread.threadListening == False:
				try:
					threading.Thread(target=self.STMThread.readFromSTM).start() # start STM listener thread
				except Exception as e:
					print("STM threading error: %s" %str(e))
					self.STMThread.isConnected = False
		# PC control loop
		'''if self.pcThread.isConnected == False:
			self.pcThread.connectToPC()
		elif self.pcThread.isConnected == True and self.pcThread.threadListening == False:
			try:
				threading.Thread(target=self.readFromPC).start() # start PC socket listener thread
			except Exception as e:
				print("PC threading error: %s" %str(e))
				self.pcThread.isConnected = False'''

	'''def multithread(self):
		#Android read and write thread
		readAndroidThread = threading.Thread(target = self.readFromAndroid, args = (), name = "read_android_thread")
		writeAndroidThread = threading.Thread(target = self.writeToAndroid, args = (), name = "write_android_thread")


		# STM read and write thread
		readSTMThread = threading.Thread(target = self.readFromSTM, args = (), name = "read_STM_thread")
		writeSTMThread = threading.Thread(target = self.writeToSTM, args = (), name = "write_STM_thread")

		# PC read and write thread
		readPCthread = threading.Thread(target = self.readFromPC, args = (), name = "read_pc_thread")
		writePCthread = threading.Thread(target = self.writeToPC, args = (), name = "write_pc_thread")

		# Set daemon for all thread      
		readPCthread.daemon = True
		writePCthread.daemon = True

		readAndroidThread.daemon = True
		writeAndroidThread.daemon = True

		readSTMThread.daemon = True
		writeSTMThread.daemon = True

		# start running the thread for PC
		readPCthread.start()

		# Start running thread for Android
		readAndroidThread.start()
 
		# Start running thread for STM
		readSTMThread.start()'''

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
			#add queue for obstacle
			#add queue for STM Manual
			self.android_queue.put(androidMessage)
			if androidMessage is not None:
				print("Read From Android: ", str(androidMessage))	

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
			self.serialMsg = self.STMThread.readFromSTM()
			if self.serialMsg is not None:
				print("Read from STM: ", str(self.serialMsg))
				
	def readTxtFile(self):
		with open('algofile.txt') as f:
			lines = f.read().splitlines()
			return lines

	def readFromPC(self):
		while True:
			pcMessage = self.pcThread.readFromPC()
			if len(pcMessage) > 0:
				print("Read From PC: ", pcMessage)
				#target = parsedMsg[0]
			if pcMessage == 'Hello from algo team':
				print("Load algorithm data..")
				self.pathReady = False
				continue	
			elif pcMessage != 'Goodbye from algo team':
				self.algoRun(pcMessage)
				self.pcThread.disconnectFromPC()
			else:
				self.pathReady = True
				self.saveToTxtFile()

	#insert strings onto list
	def algoRun(self, msg):
		parsedMsg = msg.split(',')
		if parsedMsg[0] == 'ST':
			print("Reading algorithm data: ", parsedMsg)	
			self.path_data+= parsedMsg
	#save algorithm path to text file
	def saveToTxtFile(self):
		print("Saving list to txt file. Data: ", self.path_data)
		with open('algofile.txt', 'w') as filehandle:
			for listitem in self.path_data:
				filehandle.write('%s\n' % listitem)
	#pull algorithm path to text file
	def readTxtFile(self):
		with open('algofile.txt') as f:
			lines = f.read().splitlines()
			return lines
	#not used
	def sentPath(self, coursePath):
		for index in range(self.indexPath,len(coursePath)):
			value = coursePath[index]
			if value == 'ST':
				continue
			self.writeToAndroid(value)
			#print(index, value)
			if value == 'w':
				self.indexPath = index+1
				break
	
	#execute algorithm path
	def executePath(self):
		while True:
			if not self.path_queue.empty():
				path = self.path_queue.get()
				if path == 'ST':	
					continue
				#to be removed
				#self.androidThread.writeToAndroid(path)
				elif path == 'w':
					self.pathDeployed = True
					break
				self.STMThread.writeToSTM(path)		

	def command_forwarder(self):
		while True:
			#time.sleep(0.5)
			if not self.android_queue.empty():
				msg = self.android_queue.get()


				if msg == 'START PATH' or self.pathDeployed == False:
					self.executePath(self)		
				
				#manual controls
				if msg in ["f010", "b010", "r010", "l010", "v010", "s000", "w000"]:
					self.STMThread.writeToSTM(msg)
					while True:
						if not self.rpi_queue.empty():
							msg = self.rpi_queue.get()

				#stripMsg = msg[:1]
				#if stripMsg in ["f", "b", "r", "l", "v", "s", "w"]:
				#	if int(msg[1:]) > 0 and int(msg[1:]) < 999:
						#print(stripMsg + ("%03d"  %int(msg[1:]) ))
				#		self.STMThread.writeToSTM(msg)
			#if STM send finish route
			#stop when route is finish
			#STM send message to RPI when it finally stop
			# ['target']:['payload']
			#RPI received msg to take picture
			#RPI send picture to PC
			if self.serialMsg == 'Finish Route':
				#RPI received msg to take picture
				byteMessageArr = self.takePictures(5) #RPI takes pictures and sends pictures over to PC
				for message in byteMessageArr:
					self.writeToPC(message)
				# rpi need to read from pc to get the string back
			#PC send to RPI image_id 'AN','String' or ['target']:['payload']
			#image_id send to android
			#repeat send android Msg 
			#pathDeployed = True
	
	def takePictures(self, iterations):
		camera = PiCamera()
		camera.start_preview()
		time.sleep(5) # to let the camera focus
		byteArr = []
		for i in iterations:
			filename = '/tmp/picture_' + str(i) + '.jpg'
			camera.capture(filename)
			filesize = os.path.getsize(filename)
			# send the filename and filesize
			self.socket.send(f"{filename}{SEPARATOR}{filesize}".encode())
			time.sleep(0.5) # in case camera is still moving
			with open("img.png", "rb") as image:
				f = image.read()
				b = bytearray(f)
				byteArr.append(b)

		camera.stop_preview()
		return byteArr


if __name__ == "__main__":
	print("Program Starting")
	main = RaspberryPi()	
	try:
		print("Starting MultiTreading")
		while True:
			main.run()
			#Priming
			#add STM and PC is connected
			if (main.primed is False and main.pathReady 
				and main.androidThread.isConnected
				and main.pcThread.isConnected 
				and main.STMThread.isConnected):

				main.primed = True
				time.sleep(2)
				main.writeToAndroid("READY TO START")

	except Exception as e:
		print(str(e))
		main.disconnectAll()
	except KeyboardInterrupt as e:
		print("Terminating program")
		main.disconnectAll()
		print("Program Terminated")
