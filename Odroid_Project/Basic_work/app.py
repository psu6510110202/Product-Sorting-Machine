from flask import Flask, render_template, Response
from camera import Camera       # Assuming the Camera class is defined in a file named camera.py
import aiNet                    # Import the AI model wrapper for TensorFlow Lite
import cv2
import time
import numpy as np

# Initialize the Flask app
app = Flask(__name__)

# Initialize the AI model with the quantized TensorFlow Lite model
net = aiNet.AINet("model_best_quantized.tflite")

# Dictionary to map class numbers to human-readable class names
CLASS_NAME = {
    0: "Butcher Premium",
    1: "Butcher Normal",
    2: "Butcher Shop"
}

def gen(Camera):
    """
    Video streaming generator function.
    Continuously grabs frames from the camera and processes them through AI detection.
    """
    while True:
        # Capture the current frame from the camera
        frame = Camera.get_frame()

        # Convert the JPEG image from the camera to a numpy array for AI processing
        np_frame = np.frombuffer(frame, dtype=np.uint8)
        np_frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

        # AI-based detection and classification
        start_time = time.time()

        # Perform prediction using the AI model (replace with actual prediction logic)
        classNo, certainty = net.predict(np_frame)

        # Calculate the execution time for the AI prediction
        exe_time = time.time() - start_time

        # Round the prediction certainty to two decimal places for readability
        certainty = round(certainty * 100, 2)

        # Format the prediction result for display
        result = f'Detected: {CLASS_NAME[int(classNo)]} ({certainty}%) in {exe_time:.2f} s'

        # Annotate the frame with the detection result (draw the prediction on the frame)
        np_frame = cv2.putText(np_frame, result, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Encode the frame back to JPEG format to stream over HTTP
        frame = cv2.imencode('.jpg', np_frame)[1].tobytes()

        # Yield the frame as part of the multipart HTTP response
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    """
    Home page route.
    Renders the index.html template to display the video feed.
    """
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """
    Route to stream video frames.
    This function generates video frames from the Camera class and sends them as a response.
    Use this route in the <img> tag of the index.html to display the video stream.
    """
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    # Run the Flask app, making it accessible from all network interfaces (0.0.0.0) on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
