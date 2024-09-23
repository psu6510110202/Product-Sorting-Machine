#!/usr/bin/env python
# Specifies the interpreter that should be used to run the script

from importlib import import_module
import os
from flask import Flask, render_template, Response, jsonify
import camera_opencv
import aiNet
import cv2
import serial
from flask import request
import numpy as np
import time
import socket
import argparse
import sys
import odroid_wiringpi as wpi
import requests


# Prints the number and list of arguments passed to the script
print ('Number of arguments:', len(sys.argv), 'arguments.')
print ('Argument List:', str(sys.argv))

# Argument parsing setup for command-line inputs like port name and saving images
parser = argparse.ArgumentParser(description='product sorting system')
parser.add_argument('-p', '--portname', type=str, help='port name', default='/dev/ttyACM0')
parser.add_argument('-s', '--saveimg', type=int, help='save imgs', default=0)
myparser = parser.parse_args()

#Set LED GPIO pin on Odroid via WPI interface
wpi.wiringPiSetup()
wpi.pinMode(1, 1)
wpi.pinMode(4, 1)
wpi.pinMode(5, 1)
wpi.pinMode(10, 1)

# Camera module selection
Camera = camera_opencv.Camera

# Load the AI model using the custom aiNet library
net = aiNet.AINet("model_best_quantized.tflite")

# Serial communication configuration
# Sets up the connection to an Arduino or other serial device
SERIAL = serial.Serial(
    port = myparser.portname,          # Uses the port name from the argument
    baudrate = 9600,                   # Sets baud rate for serial communication
)

# Opens the serial connection if not already open
SERIAL.isOpen()

# Threshold for detection logic
DETECTION_THRESHOLD = 500

# Class names and initial count for detected objects
CLASS_NAME = {
  0 : ("ฺButcher Premium",0),
  1 : ("Butcher Normal",0),
  2 : ("Butcher Shop",0)
}

# Initial server PWM value
serverPWM = 255

# Conveyor state (0 = stopped, 1 = running)
conveyorState = 0

# Image processing threshold values
thresh = 190
maxValue = 255 

# Configuration
UDP_IP = "192.168.91.246"  # IP address of the ESP8266 NodeMCU
UDP_PORT = 4210           # Port number on which ESP8266 is listening

# ThingSpeak API key and base URL
api_url = "https://api.thingspeak.com/update?api_key=K1JD9ZF7R8CBS60L&field"

def send_data_to_thingspeak(field_number, value):
    # Dynamically construct the field parameter (e.g., 'field1', 'field2', etc.)
    # Send the GET request
    response = requests.get(api_url + f'{field_number+1}={value}')
    
    # Check if the request was successful
    if response.status_code == 200:
        print(f"Data sent successfully to field{field_number+1}!")
    else:
        print(f"Failed to send data. Status code: {response.status_code}")

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
server_address = (UDP_IP, UDP_PORT)

# Function to apply white balance correction on the input image
def whiteBalance(img):
    result = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)  # Convert image to LAB color space
    avg_a = np.average(result[:, :, 1])            # Average of the 'a' channel (green-red component)
    avg_b = np.average(result[:, :, 2])            # Average of the 'b' channel (blue-yellow component)
    result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)  # Adjust 'a' channel
    result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)  # Adjust 'b' channel
    result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)  # Convert back to BGR color space
    return result

# Function to crop the Region of Interest (ROI) from the image
def cropROI(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # Convert to grayscale

    # Threshold the image to get a binary image
    th, bina = cv2.threshold(gray, thresh, maxValue, cv2.THRESH_BINARY)

    # Find contours in the thresholded image
    _, contours, hierarchy = cv2.findContours(bina, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    print('*******************************')
    contours_ = []
    max_x, max_y, min_x, min_y = [], [], [], []

    # Iterate over contours to find the bounding rectangle of the largest object
    for contour in contours:
        if(len(contour)>100):
            contours_.append(contour)
            contour = np.reshape(contour, [contour.shape[0],2])  # Reshape contour for easy min/max operations
            xmax, ymax = contour.max(axis=0)
            xmin, ymin = contour.min(axis=0)
            max_x.append(xmax)
            max_y.append(ymax)
            min_x.append(xmin)
            min_y.append(ymin)
    
    max_x = max(max_x)
    max_y = max(max_y)
    min_x = min(min_x)
    min_y = min(min_y)

    # Crop the image based on the detected bounding box
    crop = img[ min_y:max_y, min_x:max_x].copy()

    return crop

# Flask web app initialization
app = Flask(__name__)

# Route for the main index page
@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

# Generator function for the video stream
def gen(camera):
    """Video streaming generator function."""
    result = ''
    frame = camera.get_frame()  # Get the first frame from the camera
    productBoxes = []

    # Define 3 product boxes on the frame for tracking
    productBoxes.append(((0, frame.shape[0]-50),(frame.shape[1]/3-2, frame.shape[0]-2)))
    productBoxes.append(((frame.shape[1]/3-2, frame.shape[0]-50),(frame.shape[1]/3*2-2, frame.shape[0]-2)))
    productBoxes.append(((frame.shape[1]/3*2-2, frame.shape[0]-50),(frame.shape[1]/3*3-2, frame.shape[0]-2)))

    while True:
        outSerial = ''
        frame = camera.get_frame()                         # Capture a frame from the camera
        frame = whiteBalance(frame)                        # Apply white balance correction

        while SERIAL.inWaiting() > 0:                      # Check if any serial data is incoming
            outSerial = SERIAL.readline().decode("utf-8")  # Read data from Arduino
        
        if outSerial != '':                                # If serial data is received
            outSerial = outSerial.replace('\r\n','')
            print("Arduino=>odroid: {}".format(outSerial))

            # Pause state - capture and process an image when Arduino sends STATE_PAUSE
            if outSerial == "STATE_PAUSE" :
              time.sleep(0.5)
              frame = camera.get_frame()                   # Capture a new frame
              cv2.imwrite('imgs/img_.jpg',frame)
              crop = cropROI(frame)                        # Crop the ROI for detection
              
              if myparser.saveimg == 1:                    # Save images if the command-line flag is set
                ts = time.time()
                ts = int(ts)
                cv2.imwrite('imgs/crop_'+str(ts)+'.jpg',crop)
                print('saved {}'.format('imgs/crop_'+str(ts)+'.jpg'))
              
              # Predict the class of the object using AI model
              start_time = time.time()
              classNo, certainty = net.predict(crop)
              exe_time = time.time()-start_time
              certainty = round(certainty*100, 2)
              result = 'Detected:{}({}%) in {} s'.format(CLASS_NAME[int(classNo)][0], certainty, exe_time)
              SERIAL.write(('Detected:{}\r\n'.format(classNo)).encode())
              CLASS_NAME[int(classNo)] = (CLASS_NAME[int(classNo)][0], CLASS_NAME[int(classNo)][1] + 1)
              send_data_to_thingspeak(classNo, CLASS_NAME[int(classNo)][1])
              print(result)

            # Detected state - run conveyor and send START signal over UDP
            elif outSerial == "STATE_DETECTED":
              SERIAL.write(('RUN:'+str(serverPWM)).encode())    # Send RUN command with PWM value to Arduino
              sock.sendto(b'START', server_address)             # Send a UDP broadcast message to start the system

        frame = cv2.resize(frame, (640,480))                                                    # Resize the frame for display
        frame = cv2.putText(frame, result, (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)  # Add the result text

        # Draw the product boxes and count detected objects in each box
        cnt = 0
        for productBox in productBoxes:
          frame = cv2.rectangle(frame, 
                                (int(productBox[0][0]), int(productBox[0][1])),
                                (int(productBox[1][0]), int(productBox[1][1])),
                                (0,255,0), 2)
          frame = cv2.putText(frame, CLASS_NAME[cnt][0] + ': {}'.format(CLASS_NAME[cnt][1]), 
                              (int(productBox[0][0])+5,int((productBox[0][1]+productBox[1][1])/2)), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
          cnt = cnt+1

        frame = cv2.imencode('.jpg', frame)[1].tobytes()                # Encode frame as JPEG for streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')   # Yield the frame for the video stream

# Route for the video feed
@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route to turn off the conveyor system
@app.route('/OFF')
def OFF():
    global conveyorState
    print("html request OFF")
    SERIAL.write('OFF'.encode())            # Send OFF command to Arduino
    sock.sendto(b'STOP', server_address)    # Send STOP signal over UDP
    conveyorState = 0                       # Set conveyor state to stopped
    resp = jsonify(success=True)
    for i in range(10):
      sock.sendto(b'STOP', server_address)
    return resp

# Route to start the conveyor system
@app.route('/RUN')
def RUN():
    global conveyorState
    print("html request RUN "+str(serverPWM))
    SERIAL.write(('RUN:'+str(serverPWM)).encode())    # Send RUN command with PWM value to Arduino
    sock.sendto(b'START', server_address)             # Send START signal over UDP
    conveyorState = 1                                 # Set conveyor state to running
    resp = jsonify(success=True)
    for i in range(10):
        sock.sendto(b"START", server_address)
    return resp

# Route to update the PWM value
@app.route('/PWM')
def PWM():
    global serverPWM
    print("html update PWM {}".format(request.args['val']))
    serverPWM = int(request.args['val'])              # Update PWM value based on user input
    if conveyorState == 1:
      SERIAL.write(('RUN:'+str(serverPWM)).encode())  # Update Arduino with new PWM value if conveyor is running
    resp = jsonify(success=True)
    return resp

@app.route('/LIGHT_ON')
def LIGHT_ON():
  wpi.digitalWrite(1, 1)
  wpi.digitalWrite(4, 1)
  wpi.digitalWrite(5, 1)
  wpi.digitalWrite(10, 1)
  resp = jsonify(success=True)
  return resp

@app.route('/LIGHT_OFF')
def LIGHT_OFF():
  wpi.digitalWrite(1, 0)
  wpi.digitalWrite(4, 0)
  wpi.digitalWrite(5, 0)
  wpi.digitalWrite(10, 0)
  resp = jsonify(success=True)
  return resp

# Run the Flask app if script is executed directly
if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
