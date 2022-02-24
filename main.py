import threading
# import argparse
# import cv2
# import numpy as np
# import sys
import time
from multiprocessing import Queue

from android import *
from image import takePictures
from pc import *
from stm import *


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

        self.number_of_paths = 5

        # initialize Queue
        self.path_queue = Queue()
        self.al_pc_queue = Queue()
        self.img_pc_queue = Queue()
        self.android_queue = Queue()
        self.rpi_queue = Queue()
        self.manual_queue = Queue()

        # get algo path from txt file
        course_path = readTxtFile()

        # insert algo path to queue
        self.pathReady = self.insertPath(course_path)

        self.run()

        # run command_forwarder thread
        threading.Thread(target=self.command_forwarder).start()

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
        time.sleep(1)
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
                    self.STMThread.threadListening = True
                    thread = threading.Thread(target=self.readFromSTM)
                    thread.daemon = True
                    thread.start()  # start STM listener thread
                except Exception as error:
                    print("STM threading error: %s" % str(error))
                    self.STMThread.disconnectFromSTM()
        # PC control loop
        # if not self.pcThread.isConnected:
        #     self.pcThread.connectToPC()
        # elif self.pcThread.isConnected:
        #     if not self.pcThread.threadListening:
        #         try:
        #             self.pcThread.threadListening = True
        #             thread = threading.Thread(target=self.readFromPC)  # start PC socket listener thread
        #             thread.daemon = True
        #             thread.start()
        #         except Exception as error:
        #             print("PC threading error: %s" % str(error))
        #             self.pcThread.disconnectFromPC()

    def disconnectAll(self):
        if self.STMThread.isConnected:
            self.STMThread.disconnectFromSTM()
        if self.androidThread.isConnected:
            self.androidThread.disconnectFromAndroid()
        if self.pcThread.isConnected():
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
            serialMsg = self.STMThread.readFromSTM()
            if serialMsg is None:
                break
            print("Read from STM:", serialMsg)
            parsedMsg = serialMsg.split(',')
            # if parsedMsg[0] == 'ACK':
            #    self.rpi_queue.put(parsedMsg[0])

    def readFromPC(self):
        path_data = []
        while True:
            pcMessage = self.pcThread.readFromPC()
            if pcMessage is None:
                break
            print("Read From PC: ", pcMessage)
            # image Recognition information
            parsedMsg = pcMessage.split(',')

            if parsedMsg[0] == 'AN':
                self.android_queue.put(pcMessage)

            elif pcMessage == 'Finish Recognition':
                self.rpi_queue.put(pcMessage)

            elif pcMessage == 'A5':
                self.img_pc_queue.put(pcMessage)

            elif pcMessage == 'Not Found':
                self.img_pc_queue.put(pcMessage)

            elif pcMessage == 'Hello from algo team':
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

                # target not found
                if msg == "RPI,0":
                    movement = "l090,w000"
                    movementArr = movement.split(',')
                    for j in movementArr:
                        self.manual_queue.put(j)
                # target found
                elif msg.startswith("RPI,"):  # eg. "RPI,11"
                    print(msg)
                    imageIdStr = msg.split(",")
                    print("image id " + imageIdStr[1] + " detected!")
                    print("Task A5 completed")

                # Finish 1 path
                elif msg == 'Finish Recognition':
                    self.executePath()
                    self.number_of_paths -= 1
                    # self.android_queue.put('START PATH')
                    continue
                # elif msg == 'ACK':
                #    print("STM Movement Completed")

            if not self.android_queue.empty():
                msg = self.android_queue.get()
                parsedMsg = msg.split(',')
                if parsedMsg[0] == 'AN':
                    self.androidThread.writeToAndroid(msg)

            # Manual Controls
            if not self.manual_queue.empty() and not self.pathDeployed:
                msg = self.manual_queue.get()
                self.STMThread.writeToSTM(msg)
                time.sleep(0.1)
                continue

            if not self.al_pc_queue.empty():
                msg = self.al_pc_queue.get()
                parsedMsg = msg.split(',')
                if parsedMsg[0] == 'AL':
                    self.pcThread.writeToPC(msg)

            if not self.img_pc_queue.empty():
                msg = self.img_pc_queue.get()

                if msg == 'Start Recognition':
                    # RPI received msg to take picture
                    for i in range(5):  # RPI takes pictures and sends pictures over to PC
                        encodedString = takePictures()
                        self.writeToPC(encodedString)
                        print("image " + str(i) + "sent!")

                # Receive ACK
                elif msg == 'PC received images from RPI':
                    # Execute next path after image is taken
                    self.rpi_queue.put('START PATH')

                elif msg == "A5" or msg == 'Not Found':  # this is the checklist task
                    print("Starting A5 Task")
                    # imageIdArr = ["AN,30", "AN,30", "AN,30", "AN,20"]
                    encodedString = takePictures()
                    self.writeToPC(encodedString)  # sends image to PC
                    print("image for A5 sent!")

            # Finish all path
            if self.number_of_paths == 0:
                print("All Path is completed")
                # self.disconnectAll()
                # sys.exit()

    def testRunSTM(self):
        time.sleep(3)
        main.manual_queue.put("l100")
        main.manual_queue.put("l100")
        main.manual_queue.put("r100")
        main.manual_queue.put("r100")
        main.manual_queue.put("f100")
        # main.STMThread.writeToSTM("r100")
        # time.sleep(0.1)
        # main.STMThread.writeToSTM("r100")
        # time.sleep(0.1)
        # val = input("Insert STM Value: ")
        # time.sleep(0.3)
        # main.STMThread.writeToSTM(val)

    def testRunA5(self):
        main.img_pc_queue.put('A5')


def handler(signal_received, frame):
    # res = input("Ctrl-c was pressed. Do you really want to exit? y/n ")
    # if res == 'y':
    print("Ctrl-c was pressed. Exit ")
    try:
        main.disconnectAll()
        print("Program Interrupted")
        sys.exit(0)
    except Exception as e:
        print("Error: ", str(e))
        sys.exit(0)


if __name__ == "__main__":
    print("Program Starting")
    # signal(SIGINT, handler)
    main = RaspberryPi()
    try:
        print("Starting MultiTreading")
        main.testRunA5()
        # if main.STMThread.isConnected:
        #    main.testRunSTM()
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
