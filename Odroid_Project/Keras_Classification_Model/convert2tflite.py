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

import os
# Disable OneDNN optimizations for TensorFlow
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import tensorflow as tf
import keras
from keras.models import load_model
import glob
import cv2
import numpy as np

# Number of calibration steps for quantization
num_calibration_steps = 100

# Load all .jpg images from a specific directory for calibration (class 0 - butcher_pre)
jpegs = glob.glob('dataset/train/0_butcher_pre/*.jpg')

# Function to generate a representative dataset for quantization
def representative_dataset_gen():
    for i in range(num_calibration_steps):
        # Read and preprocess each image
        img = cv2.imread(jpegs[i])  # Load the image
        img = cv2.resize(img, (32, 32))  # Resize the image to 32x32 (input size for the model)
        img = img.astype(np.float32)  # Convert image data type to float32
        img = img / 255.0  # Normalize the image by scaling pixel values to [0, 1]
        img = np.expand_dims(img, axis=0)  # Expand dimensions to match model input shape
        yield [img]  # Yield the processed image for calibration

# Main function for model quantization and conversion to TensorFlow Lite format
def _main():

    # Path to the pre-trained Keras model
    keras_model_path = "model_best_weights.keras"

    # Load the Keras model from the saved weights file
    model = load_model(keras_model_path)

    # Create a TensorFlow Lite converter from the Keras model
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Enable optimization during conversion to reduce model size and latency
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    # Set the representative dataset for INT8 quantization (using a custom dataset generator)
    converter.representative_dataset = representative_dataset_gen
    
    # Specify that the model should support only INT8 operations
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]

    # Specify that the input and output data types of the model will be uint8 (8-bit integers)
    converter.inference_input_type = tf.uint8
    converter.inference_output_type = tf.uint8

    # Convert the Keras model to TensorFlow Lite format with INT8 quantization
    tflite_model = converter.convert()

    # Save the quantized model to a .tflite file
    with open("./model_best_quantized.tflite", "wb") as f:
        f.write(tflite_model)

# Run the main function if this script is executed directly
if __name__ == '__main__':
    _main()
