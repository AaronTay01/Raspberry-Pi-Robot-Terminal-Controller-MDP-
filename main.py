from stm import *
from android import *
from pc import *
import threading
import os
from utils import format_for
from multiprocessing import Process, Queue
from picamera import PiCamera
from multiprocessing import Queue

# import argparse
# import cv2
# import numpy as np
# import sys
import time


def readTxtFile():
    with open('algo file.txt') as f:
        lines = f.read().splitlines()
        return lines


def saveToTxtFile(path_data):
    print("Saving list to txt file. Data: ", path_data)
    with open('algo file.txt', 'w') as fileHandle:
        for item in path_data:
            fileHandle.write('%s\n' % item)

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096 # send 4096 bytes each time step

class RaspberryPi(threading.Thread):
    def __init__(self):
        super().__init__()
        self.STMThread = STMRobot()
        self.pcThread = PCInterface()
        self.androidThread = AndroidApplication()

        # True if everything is ready to Start
        self.primed = False

        # True if path is being deployed
        self.pathDeployed = False

        self.number_of_paths = 5

        # initialize Queue
        self.path_queue = Queue()
        self.al_pc_queue = Queue()
        self.img_pc_queue = Queue()
        self.android_queue = Queue()
        self.rpi_queue = Queue()
        self.manual_queue = Queue()

        # run command_forwarder thread
        threading.Thread(target=self.command_forwarder).start()

        # get algo path from txt file
        course_path = readTxtFile()

        # insert algo path to queue
        self.pathReady = self.insertPath(course_path)

        # serial Received Message
        self.serialMsg = None

    # print algo path from queue (Only for testing)
    def printPath(self):
        while True:
            if not self.path_queue.empty():
                msg = self.path_queue.get()
                print(msg)
            else:
                break

    # insert path from text file onto queue
    def insertPath(self, course_path):
        for i in course_path:
            # print(i)
            self.path_queue.put(i)
        # check list is not empty
        if course_path:
            return True
        else:
            return False

    # threading
    def run(self):
        # Android control loop
        if not self.androidThread.isConnected:
            self.androidThread.connectToAndroid()
        elif self.androidThread.isConnected:
            if not self.androidThread.threadListening:
                try:
                    threading.Thread(target=self.readFromAndroid).start()  # start Android socket listener thread
                except Exception as error:
                    print("Android threading error: %s" % str(error))
                    self.androidThread.disconnectFromAndroid()
        # STM control loop
        if not self.STMThread.isConnected:
            self.STMThread.connectToSTM()
        elif self.STMThread.isConnected:
            if not self.STMThread.threadListening:
                try:
                    threading.Thread(target=self.readFromSTM).start()  # start STM listener thread
                except Exception as error:
                    print("STM threading error: %s" % str(error))
                    self.STMThread.disconnectFromSTM()
        # PC control loop
        if not self.pcThread.isConnected:
            self.pcThread.connectToPC()
        elif self.pcThread.isConnected:
            if not self.pcThread.threadListening:
                try:
                    threading.Thread(target=self.readFromPC).start()  # start PC socket listener thread
                except Exception as error:
                    print("PC threading error: %s" % str(error))
                    self.pcThread.disconnectFromPC()

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
            # add queue for obstacle
            if androidMessage is not None:
                print("Read From Android: ", str(androidMessage))
                parsedMsg = androidMessage.split(',')
                # Manual Controls
                if androidMessage in ["f010", "b010", "r010", "l010", "v010", "s000", "w000"]:
                    self.manual_queue.put(androidMessage)
                # Obstacle Information
                if parsedMsg[0] == 'AL':
                    self.al_pc_queue.put(androidMessage)
                # Start STM (Start Button Initialize)
                if androidMessage == 'START PATH':
                    self.rpi_queue.put(androidMessage)

    def writeToPC(self, message):
        if self.pcThread.isConnected and message is not None:
            self.pcThread.writeToPC(message)

    def writeToSTM(self, message):
        if self.STMThread.isConnected and message:
            self.STMThread.writeToSTM(message)
            return True
        return False

    def readFromSTM(self):
        while True:
            self.serialMsg = self.STMThread.readFromSTM()
            if self.serialMsg is not None:
                print("Read from STM: ", str(self.serialMsg))
                if self.serialMsg != 'ACK':
                    self.rpi_queue.put(self.serialMsg)

    def readFromPC(self):
        path_data = []
        while True:
            pcMessage = self.pcThread.readFromPC()
            if pcMessage is not None:
                # image Recognition information
                parsedMsg = pcMessage.split(',')

                if parsedMsg[0] == 'AN':
                    self.android_queue.put(pcMessage)

                elif pcMessage == 'Finish Recognition':
                    self.rpi_queue.put(pcMessage)

                if pcMessage == 'Hello from algo team':
                    print("Load algorithm data..")
                    with self.path_queue.mutex:
                        self.path_queue.queue.clear()
                    self.pathReady = False
                    continue
                # save and terminate
                elif pcMessage == 'Goodbye from algo team':
                    saveToTxtFile(path_data)
                    course_path = readTxtFile()
                    self.pathReady = self.insertPath(course_path)  # insert path onto queue
                    self.pcThread.disconnectFromPC()
                elif not self.pathReady:
                    parsedMsg = pcMessage.split(',')
                    if parsedMsg[0] == 'ST':
                        print("Reading algorithm data: ", parsedMsg)
                        path_data += parsedMsg
                    # path_data = self.getAlgoData(pcMessage, path_data)  # insert msg onto path_data list

    @staticmethod
    def getAlgoData(msg, path_data):
        parsedMsg = msg.split(',')
        if parsedMsg[0] == 'ST':
            print("Reading algorithm data: ", parsedMsg)
            path_data += parsedMsg
            return path_data
        return path_data

    # execute algorithm path
    def executePath(self):
        while True:
            if not self.path_queue.empty():
                path = self.path_queue.get()
                if path == 'ST':
                    path = self.path_queue.get()
                    self.STMThread.writeToSTM(path)
                elif path == 'w':
                    self.img_pc_queue.put('Start Recognition')
                    break

    def command_forwarder(self):
        while True:

            if not self.rpi_queue.empty():
                msg = self.rpi_queue.get()
                # Start Button
                if msg == 'START PATH':
                    self.executePath()
                    self.pathDeployed = True
                    continue

                # Finish 1 path
                if msg == 'Finish Recognition':
                    self.executePath()
                    self.number_of_paths -= 1
                    # self.android_queue.put('START PATH')
                    continue

            if not self.android_queue.empty():
                msg = self.android_queue.get()
                parsedMsg = msg.split(',')
                if parsedMsg[0] == 'AN':
                    self.androidThread.writeToAndroid(msg)

            # Manual Controls
            if not self.manual_queue.empty() and not self.pathDeployed:
                msg = self.manual_queue.get()
                self.STMThread.writeToSTM(msg)
                while True:
                    if self.serialMsg == 'ACK':
                        break
                continue

            if not self.al_pc_queue.empty():
                msg = self.al_pc_queue.get()
                parsedMsg = msg.split(',')
                if parsedMsg[0] == 'AL':
                    self.pcThread.writeToPC(msg)

            if not self.img_pc_queue.empty():
                msg = self.img_pc_queue.get()
                if msg == 'Finish Route':
                    # RPI received msg to take picture
                    byteMessageArr = self.takePictures(5)  # RPI takes pictures and sends pictures over to PC
                    for message in byteMessageArr:
                        self.writeToPC(message)
                    continue
            # Finish all path
            if self.number_of_paths is 0:
                print("All Path is completed")
                # self.disconnectAll()
                # sys.exit()

    def takePictures(self, iterations):
        camera = PiCamera()
        camera.start_preview()
        time.sleep(5)  # to let the camera focus
        byteArr = []
        for i in iterations:
            filename = '/tmp/picture_' + str(i) + '.jpg'
            camera.capture(filename)
            filesize = os.path.getsize(filename)
            # send the filename and filesize
            self.socket.send(f"{filename}{SEPARATOR}{filesize}".encode())
            time.sleep(0.5)  # in case camera is still moving
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
            # Priming
            # add STM and PC is connected
            if (not main.primed and main.pathReady
                    and main.androidThread.isConnected
                    and main.pcThread.isConnected
                    and main.STMThread.isConnected):
                main.primed = True
                time.sleep(2)
                main.writeToAndroid("READY TO START")
                print("System All Green")

    except Exception as e:
        print(str(e))
        main.disconnectAll()
    except KeyboardInterrupt as e:
        print("Terminating program")
        main.disconnectAll()
        print("Program Terminated")
