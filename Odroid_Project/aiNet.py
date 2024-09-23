import os
# Disable certain TensorFlow optimizations (optional)
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Import necessary libraries
import tensorflow as tf           # TensorFlow for handling models and predictions
from PIL import Image             # For handling images
import numpy as np                # For array operations
import cv2                        # For image processing
from tensorflow.lite.python import interpreter as interpreter_wrapper  # To use TensorFlow Lite interpreter
import time                       # For measuring execution time

# Constants for image normalization
IMAGE_MEAN = 0.0
IMAGE_STD = 255.0

class AINet(object):
    """Class for handling AI model prediction with TensorFlow Lite."""

    def __init__(self, model_dir):
        """
        Initialize the TensorFlow Lite interpreter and allocate tensors.
        
        Parameters:
        - model_dir: The path to the TensorFlow Lite model (.tflite file).
        """
        # Load the TensorFlow Lite model into the interpreter
        self.interpreter = interpreter_wrapper.Interpreter(model_path=model_dir)
        
        # Allocate memory for the model's tensors (input/output data)
        self.interpreter.allocate_tensors()

        # Retrieve the details of the model's input and output layers
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # Print the input and output details for debugging purposes
        print(self.input_details)
        print(self.output_details)

    def predict(self, img, quantized=True):
        """
        Perform AI prediction on the input image.
        
        Parameters:
        - img: The input image in numpy array format.
        - quantized: A flag indicating whether the model expects quantized input.
        
        Returns:
        - idex[0][0]: The index of the class with the highest probability.
        - out / 255: The confidence of the prediction (normalized).
        """
        # Ensure the input image is a NumPy array (necessary for further processing)
        if not isinstance(img, np.ndarray):
            img = np.array(img)

        # Resize the input image to match the model's input size (32x32)
        resized_image = cv2.resize(img, (32, 32), cv2.INTER_AREA)

        # If the model is not quantized, normalize the image
        if not quantized:
            resized_image = resized_image.astype('float32')
            # Subtract the mean and divide by the standard deviation (standard normalization)
            mean_image = np.full((32, 32), IMAGE_MEAN, dtype='float32')
            resized_image = (resized_image - mean_image) / IMAGE_STD

        # Add a batch dimension to the image (model expects batches)
        resized_image = resized_image[np.newaxis, ...]

        # Start the timer to measure prediction time
        start_time = time.time()

        # Set the input tensor for the interpreter with the processed image
        self.interpreter.set_tensor(self.input_details[0]['index'], resized_image)
        
        # Run the interpreter (perform the prediction)
        self.interpreter.invoke()

        # Get the prediction output from the output tensor
        output_data0 = self.interpreter.get_tensor(self.output_details[0]['index'])
        
        # Squeeze the output to remove unnecessary dimensions
        output_data0 = np.squeeze(output_data0)

        # Convert the output data to float for easier handling
        output_data0 = output_data0.astype(float)

        # Find the class with the highest predicted probability
        out = np.amax(output_data0)
        idex = np.where(output_data0 == out)

        # Return the index of the predicted class and the confidence (scaled to 0-1 range)
        return idex[0][0], out / 255


def testAI():

  img = cv2.imread('./test_images/image1.jpg')
  image_org = img
  net = AINet("./pretrained_model/model_best_quantized.tflite")
  idex,out = net.predict(img)

  print('{}:{}%'.format(idex,out))

if __name__ == '__main__':
  testAI()