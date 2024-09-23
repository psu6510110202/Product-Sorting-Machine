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
from tensorflow.keras import applications, optimizers
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dropout, Flatten, Dense, Input
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# Set GPU memory fraction (optional)
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        # Set TensorFlow to use only as much GPU memory as needed
        tf.config.experimental.set_memory_growth(gpus[0], True)
        
        # Set a limit of 6GB for GPU memory usage
        tf.config.experimental.set_virtual_device_configuration(
            gpus[0],
            [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=6144)]
        )
    except RuntimeError as e:
        print(e)  # Handle errors that occur if GPUs are already initialized

# Print TensorFlow version
print(tf.__version__)

# Check if a GPU is being used
print("***************************************device***************************************")
if tf.test.gpu_device_name():
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))
else:
    print("Please install GPU version of TensorFlow")
print("***************************************device***************************************")


# Set image dimensions
img_width, img_height = 32, 32

# Define directories for training and validation datasets
train_data_dir = 'dataset/train'
validation_data_dir = 'dataset/validation'

# Set number of epochs, batch size, and number of output classes
epochs = 100
batch_size = 64
classes = 3

# Load VGG16 pre-trained model without the top classification layers
input_tensor = Input(shape=(img_width, img_height, 3))
base_model = applications.VGG16(weights='imagenet', 
                                include_top=False, 
                                input_tensor=input_tensor)

# Create the classification layers to add on top of the VGG16 base
x = Flatten()(base_model.output)                            # Flatten the output
x = Dense(256, activation='relu')(x)                        # Fully connected layer with 256 neurons
x = Dropout(0.5)(x)                                         # Dropout layer to prevent overfitting
output_tensor = Dense(classes, activation='softmax')(x)     # Output layer with softmax for classification

# Create the final model combining the VGG16 base and the custom top layers
new_model = Model(inputs=base_model.input, outputs=output_tensor)

# Lock the first 15 layers of VGG16 so they are not trainable
for layer in base_model.layers[:15]:
    layer.trainable = False

# Display the model architecture
new_model.summary()

# Compile the model with loss function, optimizer, and metrics
new_model.compile(loss='categorical_crossentropy',
                  optimizer=optimizers.SGD(learning_rate=0.01, momentum=0.9),
                  metrics=['accuracy'])

# Create image data generators for training and validation, with image rescaling
train_datagen = ImageDataGenerator(rescale=1./255)
validation_datagen = ImageDataGenerator(rescale=1./255)

# Set up the generators to read images from the dataset directories
train_generator = train_datagen.flow_from_directory(
    train_data_dir,
    target_size=(img_height, img_width),                # Resize images to match model input size
    batch_size=batch_size,
    class_mode='categorical',                           # Multi-class classification
    shuffle=True)                                       # Shuffle training data

validation_generator = validation_datagen.flow_from_directory(
    validation_data_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    class_mode='categorical')

# Calculate steps per epoch for both training and validation
STEP_SIZE_TRAIN = train_generator.n // train_generator.batch_size
STEP_SIZE_VALID = validation_generator.n // validation_generator.batch_size

# Set up early stopping to prevent overfitting by stopping training when the loss doesn't improve
early_stop = EarlyStopping(monitor='loss', min_delta=0.001, patience=3, mode='min', verbose=1)

# Save the best model weights during training
checkpoint = ModelCheckpoint('model_best_weights.keras', monitor='loss', verbose=1, save_best_only=True, mode='min')

# Train the model using the training and validation data generators
new_model.fit(
    train_generator,
    steps_per_epoch=STEP_SIZE_TRAIN,                # Number of batches to process per epoch
    epochs=epochs,                                  # Number of epochs to train
    validation_data=validation_generator,           # Validation data to evaluate the model
    validation_steps=STEP_SIZE_VALID,               # Number of validation batches per epoch
    callbacks=[early_stop, checkpoint])             # Callbacks for early stopping and model checkpointing
