# BSD 2-Clause License
# 
# Copyright (c) 2020, ANM-P4F
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ==============================================================================

import time
import cv2
import numpy as np
from tensorflow.lite.python import interpreter as interpreter_wrapper

# Path to the quantized TensorFlow Lite model
model_path = 'model_best_quantized.tflite'

# Initialize the TensorFlow Lite interpreter with the quantized model
interpreter = interpreter_wrapper.Interpreter(model_path=model_path)

# Allocate memory for the model's tensors (required before using the interpreter)
interpreter.allocate_tensors()

# Get details about the model's input and output tensors
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Print the input and output details for debugging and verification purposes
print(input_details)
print(output_details)

# Infinite loop for continuously taking images as input
while 1:

  # Prompt the user for the path to an image file
  imgPath = input("input image: ")

  # Exit the loop if no input is provided
  if imgPath == "":
    break

  # Load the image using OpenCV
  img = cv2.imread(imgPath)

  # Resize the image to match the model's input shape (32x32)
  img = cv2.resize(img, (32, 32))

  # Add a batch dimension to the image (since the model expects batches)
  img = img[np.newaxis, ...]

  # Measure the time taken for the prediction
  start_time = time.time()

  # Set the input tensor for the interpreter (feeds the image into the model)
  interpreter.set_tensor(input_details[0]['index'], img)

  # Invoke the interpreter to make a prediction
  interpreter.invoke()

  # Get the output tensor (the model's prediction result)
  output_data0 = interpreter.get_tensor(output_details[0]['index'])

  # Convert the output to a floating-point number for easier interpretation
  output_data0 = output_data0.astype(float)

  # Normalize the output by dividing it by 255 (since it's scaled as uint8)
  print(output_data0 / 255)

  # Print the time taken for the prediction
  print("--- %s seconds ---" % (time.time() - start_time))