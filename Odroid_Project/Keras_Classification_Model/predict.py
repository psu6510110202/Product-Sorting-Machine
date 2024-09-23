import os
# Disable OneDNN optimizations for TensorFlow
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import cv2
import glob
from keras.models import load_model
import numpy as np
import time
import tensorflow as tf

# Configuring GPU options
physical_devices = tf.config.experimental.list_physical_devices('GPU')
if physical_devices:
    for device in physical_devices:
        # Enable memory growth so TensorFlow only allocates memory as needed
        tf.config.experimental.set_memory_growth(device, True)

    # Optional: Limit the GPU memory usage to 70% of the total GPU memory
    tf.config.experimental.set_virtual_device_configuration(
        physical_devices[0],
        [tf.config.experimental.VirtualDeviceConfiguration(
            memory_limit=0.7 * tf.config.experimental.get_memory_info(device)['total']
        )]
    )

# Load the trained Keras model from the saved weights file
model = load_model('model_best_weights.keras')

# Infinite loop to process multiple images
while True:
    # Prompt the user to input the path to an image file
    imgPath = input("input image: ")

    # Break the loop if no input is provided
    if imgPath == "":
        break

    # Load the image using OpenCV
    img = cv2.imread(imgPath)

    # Resize the image to the expected input size of the model (32x32)
    img = cv2.resize(img, (32, 32))

    # Convert the image data type to float32 for processing
    img = img.astype(np.float32)

    # Normalize the image pixel values to the range [0, 1]
    img = img / 255.0

    # Add a batch dimension to the image (since the model expects a batch of images)
    img = np.expand_dims(img, axis=0)

    # Measure the time it takes for the model to make a prediction
    start_time = time.time()

    # Use the model to predict the class probabilities of the input image
    result = model.predict(img)

    # Remove unnecessary dimensions from the prediction result
    result = np.squeeze(result)

    # Print the raw result of the model's prediction
    print(result)

    # Round the probabilities to two decimal places for easier interpretation
    result = (round(result[0], 2), round(result[1], 2), round(result[2], 2))

    # Print the time taken for the prediction
    print("--- %s seconds ---" % (time.time() - start_time))

    # Print the rounded result probabilities
    print(result)

    # Check the prediction and print a message based on the class with the highest probability
    if result[0] == 1.0:
        print("Predict : It's Butcher Premium")
    if result[1] == 1.0:
        print("Predict : It's Butcher Normal")
    if result[2] == 1.0:
        print("Predict : It's Butcher Shop")
