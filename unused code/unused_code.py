def multithread(self):
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
    readSTMThread.start()

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

				#stripMsg = msg[:1]
				#if stripMsg in ["f", "b", "r", "l", "v", "s", "w"]:
				#	if int(msg[1:]) > 0 and int(msg[1:]) < 999:
						#print(stripMsg + ("%03d"  %int(msg[1:]) ))
				#		self.STMThread.writeToSTM(msg)

def algoRun(self, msg):
    if msg != 'terminate':
        parsedMsg = msg.split(',')
        print("Reading algorithm data: ", parsedMsg)	
        self.path_data+= parsedMsg
    else:
        print("Saving list to txt file. Data: ", self.path_data)
        with open('algofile.txt', 'w') as filehandle:
            for listitem in self.path_data:
                filehandle.write('%s\n' % listitem)