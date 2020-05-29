import dlib
import cv2
import numpy as np
import imutils
from imutils.video import WebcamVideoStream
from imutils.video import FPS
from PIL import Image
import serial
from datetime import datetime
import threading
import pytesseract
import time
import requests

serial_port = '/dev/ttyACM0'
cam_id = 0

arduino = serial.Serial(serial_port, 9600)
arduino.write('n'.encode('ascii'))
time.sleep(1)
print("loading...")

detector1 = dlib.simple_object_detector('paper.svm')

vehicle1_number = ''
vehicle2_number = ''

vehicle1_intime = ''
vehicle2_intime = ''

webcam = WebcamVideoStream(src=cam_id).start()
chk = False


def detectNoPlate():
    current = ''
    previous = ''
    number = ''
    count = 0
    fps = FPS().start()
    while True:
        im = webcam.read()
        im = imutils.resize(im, width=400)
        orig = im.copy()

        bgray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(bgray)

        nimage = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        roi = detector1(nimage)
        key = cv2.waitKey(1) & 0xFF

        for i in roi:
            (x, y, w, h) = (i.left(), i.top(), i.right(), i.bottom())
            cv2.rectangle(orig, (x, y), (w, h), (0, 255, 0), 2)
            cv2.putText(im, 'plate detected', (x - 10, y - 10), cv2.FONT_HERSHEY_PLAIN, 1.2, (0, 255, 0), 2)
            cv2.rectangle(im, (x, y), (w, h), (0, 255, 0), 2)
            cv2.imwrite("roi1.png", gray[y:y + w, x:x + h])
            text = pytesseract.image_to_string(Image.open('roi1.png'))
            # text = "123"
            print("found text: ", text)
            if count == 0:
                if len(text) != 0:
                    current = text
                    previous = 0
                    count += 1
            else:
                if len(text) != 0:
                    previous = current
                    current = text

            if current == text and previous == text and len(text) != 0:
                count += 1

        if count == 5:
            print("confirmed: ", current)
            fps.stop()
            number = current
            cv2.destroyAllWindows()
            break
        cv2.imshow("Image", np.hstack([im]))
        if key == ord('q'):
            fps.stop()
            cv2.destroyAllWindows()
            exit(0)
            break
        fps.update()

    if number != '':
        return number

        # DoRequests({"status": "out", "vehicle": "vehicle1", "number": vehicle1_number, 'charge': '10'}).start()


class DoRequests(threading.Thread):
    def __init__(self, data):
        self.data = data
        threading.Thread.__init__(self)

    def run(self):
        self.url = 'https://projects.aimtechs.co.in/num-plate-webapp/api/callback?authkey=B94xHaZbQx'
        self.r = requests.post(url=self.url, json=self.data)
        print(self.r.json())


class MainThread(threading.Thread):
    def __init__(self, runnable):
        threading.Thread.__init__(self)
        self.runnable = runnable

    def run(self):
        global arduino, chk, vehicle1_number, vehicle2_number, vehicle2_intime, vehicle1_intime, new_vehicle_status, current_vehicles
        print("started..")
        while self.runnable:
            rd = arduino.read().decode('ascii')
            if rd == 'X':
                plate = detectNoPlate()
                print("num plate found! \nChecking for available parking space..")
                arduino.write('S'.encode('ascii'))
                current_vehicles = arduino.read().decode('ascii')
                print('Data Received: ', current_vehicles)
                if current_vehicles == 'A' or current_vehicles == 'B' or current_vehicles == 'C':  # check for avail space
                    print("parking space found..")
                    arduino.write('O'.encode('ascii'))
                    print("opening gate...")
                    time.sleep(2.5)
                    print("waiting for car to get parked...")  # watiting for charector from arduino
                    while True:
                        arduino.write('S'.encode('ascii'))
                        new_vehicle_status = arduino.read().decode('ascii')
                        if new_vehicle_status != current_vehicles:
                            break
                    print("vehicle parked!", new_vehicle_status)  ## status updated
                    chk = True
                    if new_vehicle_status == 'B':
                        vehicle2_intime = datetime.now()
                        vehicle2_number = plate
                        DoRequests({"status": "in", "vehicle": "vehicle1", "number": plate}).start()
                    if new_vehicle_status == 'C':
                        vehicle1_intime = datetime.now()
                        vehicle1_number = plate
                        DoRequests({"status": "in", "vehicle": "vehicle2", "number": plate}).start()
                    if new_vehicle_status == "D":
                        if vehicle1_number != '':
                            vehicle2_intime = datetime.now()
                            vehicle2_number = plate
                            DoRequests({"status": "in", "vehicle": "vehicle2", "number": plate}).start()
                        elif vehicle2_number != '':
                            vehicle1_intime = datetime.now()
                            vehicle1_number = plate
                            DoRequests({"status": "in", "vehicle": "vehicle1", "number": plate}).start()
                else:
                    print("there is no available parking space!!")
                    time.sleep(2)

            elif rd == 'Y' and chk:
                arduino.write('O'.encode('ascii'))
                time.sleep(2) # was 4
                arduino.write('S'.encode('ascii'))
                data_came = arduino.read().decode('ascii')
                if data_came == 'A':  # both gone
                    print('both vehicle slots empty')
                    if vehicle2_number == '':
                        diff = datetime.now() - vehicle1_intime
                        DoRequests({"status": "out", "vehicle": "vehicle1", "number": vehicle1_number, "charge": diff}).start()
                        vehicle1_number = ''
                        vehicle1_intime = ''
                        print("vehicle 1 gone...")
                    elif vehicle1_number == '':
                        diff = datetime.now() - vehicle2_intime
                        DoRequests({"status": "out", "vehicle": "vehicle2", "number": vehicle2_number, "charge": diff}).start()
                        vehicle2_number = ''
                        vehicle2_intime = ''
                        print("vehicle 2 gone..")

                if data_came == 'C':  # veh2 gone
                    diff = datetime.now() - vehicle2_intime
                    DoRequests({"status": "out", "vehicle": "vehicle2", "number": vehicle2_number, "charge": diff}).start()
                    vehicle2_number = ''
                    vehicle2_intime = ''
                    print("vehicle 2 gone...")
                if data_came == 'B':  # veh1 gone
                    diff = datetime.now() - vehicle1_intime
                    DoRequests({"status": "out", "vehicle": "vehicle1", "number": vehicle1_number, "charge": diff}).start()
                    vehicle1_number = ''
                    vehicle1_intime = ''
                    print("vehicle 1 gone...")



main_thread = MainThread(True)
main_thread.start()
main_thread.join()
