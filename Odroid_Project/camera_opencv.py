import os
import cv2
from base_camera import BaseCamera  # Import the BaseCamera class to inherit functionality

# Camera class extends the BaseCamera class to provide video capture using OpenCV
class Camera(BaseCamera):
    # Default values for video source and resolution
    video_source = 1            # Default video source (0 would be the first camera, 1 could be a second camera)
    video_width = 640           # Default video frame width
    video_height = 480          # Default video frame height

    def __init__(self):
        # Check if the 'OPENCV_CAMERA_SOURCE' environment variable is set; if so, use that as the video source
        if os.environ.get('OPENCV_CAMERA_SOURCE'):
            Camera.set_video_source(int(os.environ['OPENCV_CAMERA_SOURCE']))    # Set video source from the environment variable
        super(Camera, self).__init__()                                          # Call the parent class constructor (BaseCamera)

    @staticmethod
    def set_video_source(source):
        """Set the video source, such as a camera index or a video file."""
        Camera.video_source = source  # Update the class's video source variable

    # The 'frames' method provides continuous access to frames from the camera as a generator
    @staticmethod
    def frames(zoom_factor=1.0):
        """Captures frames from the camera and optionally applies a zoom effect."""
        # Open the camera with the specified video source
        camera = cv2.VideoCapture(Camera.video_source)
        
        # Set the resolution of the camera frames
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, Camera.video_width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Camera.video_height)
        
        # Check if the camera was successfully opened
        if not camera.isOpened():
            raise RuntimeError('Could not start camera.')  # Raise an error if the camera couldn't be started

        while True:
            # Capture the current frame from the camera
            ret, img = camera.read()
            if not ret:
                break                                       # If capturing the frame failed, exit the loop

            # Get the height and width of the frame (img.shape returns a tuple: height, width, and color channels)
            height, width, _ = img.shape

            # If a zoom factor greater than 1.0 is applied, zoom the image by cropping and resizing
            if zoom_factor > 1.0:
                # Calculate new dimensions based on the zoom factor
                new_width = int(width / zoom_factor)
                new_height = int(height / zoom_factor)
                
                # Calculate the coordinates to crop the center of the image
                x1 = (width - new_width) // 2
                y1 = (height - new_height) // 2
                x2 = x1 + new_width
                y2 = y1 + new_height

                # Crop the frame to the calculated coordinates
                img = img[y1:y2, x1:x2]

                # Resize the cropped frame back to the original dimensions
                img = cv2.resize(img, (width, height))

            # Yield the current frame to be used in video streaming
            yield img
