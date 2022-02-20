from stm import *
from android import *
from pc import *
import threading
import os
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

        # initialize Queue
        self.path_queue = Queue()
        self.pc_queue = Queue()
        self.android_queue = Queue()
        self.rpi_queue = Queue()

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
            # add queue for STM Manual
            if androidMessage is not None:
                self.android_queue.put(androidMessage)
                print("Read From Android: ", str(androidMessage))

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

    def readFromPC(self):
        path_data = []
        while True:
            pcMessage = self.pcThread.readFromPC()
            if pcMessage is not None:
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
                    self.getAlgoData(pcMessage, path_data)  # insert msg onto path_data list
                # image Recognition
                if pcMessage == 'AL':
                    self.writeToAndroid(pcMessage)

    # insert strings onto list
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
                    self.pathDeployed = True
                    self.pc_queue.put('Start Recognition')
                    break

    def command_forwarder(self):
        while True:
            if not self.android_queue.empty():
                msg = self.android_queue.get()
                if msg == 'START PATH':
                    self.executePath()

                # manual controls
                if msg in ["f010", "b010", "r010", "l010", "v010", "s000", "w000"]:
                    self.STMThread.writeToSTM(msg)
                    while True:
                        if self.serialMsg == 'ACK':
                            break
            if not self.pc_queue.empty():
                msg = self.pc_queue.get()
                if msg == 'Start Recognition':
                    self.writeToPC(msg)

            # if STM send finish route
            # stop when route is finish
            # STM send message to RPI when it finally stop
            # ['target']:['payload']
            # RPI received msg to take picture
            # RPI send picture to PC
            if self.serialMsg == 'Finish Route':
                # RPI received msg to take picture
                byteMessageArr = self.takePictures(5)  # RPI takes pictures and sends pictures over to PC
                for message in byteMessageArr:
                    self.writeToPC(message)
        # rpi need to read from pc to get the string back

    # PC send to RPI image_id 'AN','String' or ['target']:['payload']
    # image_id send to android
    # repeat send android Msg
    # pathDeployed = True

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

    except Exception as e:
        print(str(e))
        main.disconnectAll()
    except KeyboardInterrupt as e:
        print("Terminating program")
        main.disconnectAll()
        print("Program Terminated")
