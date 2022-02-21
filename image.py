from picamera import PiCamera
import time
import io
from PIL import Image
import socket
import base64

server_socket = socket.socket()
server_socket.bind(('192.168.38.1', 5001))
server_socket.listen(0)

print('Server listening....') 
conn, addr = server_socket.accept()       # Establish connection with client. 
print('Got connection from', addr)

def takePictures():
    # Create the in-memory stream 
    stream = io.BytesIO() 
    with PiCamera() as camera: 
        camera.resolution = (640,480)
        camera.start_preview() 
        time.sleep(2) 
        camera.capture(stream, format='jpeg') 
    # "Rewind" the stream to the beginning so we can read its content 
    stream.seek(0) 
    image = Image.open(stream)
    image.save('tmp/image.jpeg', 'jpeg')
    file = open("tmp/image.jpeg", "rb")
    encodedString = base64.b64encode(file.read())
    remainder = len(encodedString) % 1024
    emptyString = " " * (remainder)
    emptyString = str.encode(emptyString)
    encodedString = encodedString + emptyString
    return encodedString
