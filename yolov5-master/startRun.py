from itertools import count
import time
import os 
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from os import listdir
from os.path import isfile, join
from PIL import Image
import glob

class Event(LoggingEventHandler): 
    def on_created(self, event):
        rec_path = './images/received'
        rec_images = [join(rec_path, f) for f in listdir(rec_path) if isfile(join(rec_path, f))]
        if len(rec_images)!=0:
            print("\n------------------------\nNew image(s) received!\n------------------------\n")
            os.system('python detect.py --weights best_v3_2.pt --img 416 --conf 0.4 --source ./images/received --save-txt --save-conf')
        
            exp_path = './runs/detect/collage'
            listofimages = [join(exp_path, f) for f in listdir(exp_path) if isfile(join(exp_path, f))]
            if len(listofimages)==5:
                create_collage(exp_path, 6144, 3072, listofimages)

def create_collage(path, width, height, listofimages):
    cols = 3
    rows = 2
    thumbnail_width = width//cols
    thumbnail_height = height//rows
    size = thumbnail_width, thumbnail_height
    new_im = Image.new('RGB', (width, height))
    ims = []
    for p in listofimages:
        im = Image.open(p)
        im.thumbnail(size)
        ims.append(im)
    i = 0
    x = 0
    y = 0
    for col in range(cols):
        for row in range(rows):
            # print(i, x, y)
            if(i<len(listofimages)):
                new_im.paste(ims[i], (x, y))
                i += 1
                y += thumbnail_height
        x += thumbnail_width
        y = 0

    print("Collage saved!")
    new_im.save(path+"/Collage.jpg")


if __name__ == "__main__":
    path = './images/received'

    files = glob.glob('./images/detected/*')
    for f in files:
        os.remove(f)

    pics = glob.glob('./runs/detect/exp/*')
    for p in pics:
        os.remove(p)

    event_handler = Event()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()