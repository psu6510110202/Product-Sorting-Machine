import cv2  # OpenCV for capturing and processing images
from base_camera import BaseCamera  # Importing the BaseCamera class to extend it

class Camera(BaseCamera):
    @staticmethod
    def frames(zoom_factor=1.8):  # Zoom factor controls how much the image is zoomed in (default is 1.8x)
        # Initialize the camera (1 is used to indicate a secondary camera; 0 is for the default camera)
        camera = cv2.VideoCapture(1)  

        # Check if the camera opened successfully
        if not camera.isOpened():
            raise RuntimeError('Could not start camera.')

        # Continuously capture frames from the camera
        while True:
            # Read a frame from the camera
            ret, img = camera.read()

            # If frame capturing failed, raise an error
            if not ret:
                raise RuntimeError('Failed to read frame from camera.')

            # Get the dimensions of the image (height, width, and number of channels)
            height, width, _ = img.shape

            # Calculate the center of the image
            center_x, center_y = width // 2, height // 2

            # Calculate new dimensions for cropping (based on the zoom factor)
            new_width = int(width / zoom_factor)
            new_height = int(height / zoom_factor)

            # Determine the crop boundaries while ensuring they do not exceed the image dimensions
            x1 = max(center_x - new_width // 2, 0)  # Left boundary
            y1 = max(center_y - new_height // 2, 0)  # Top boundary
            x2 = min(center_x + new_width // 2, width)  # Right boundary
            y2 = min(center_y + new_height // 2, height)  # Bottom boundary

            # Crop the image around the center (simulating a zoom by removing outer regions)
            cropped_img = img[y1:y2, x1:x2]

            # Resize the cropped image back to the original dimensions
            # This creates the zoom effect by resizing the zoomed-in region
            zoomed_img = cv2.resize(cropped_img, (width, height), interpolation=cv2.INTER_LINEAR)

            # Encode the zoomed frame as a JPEG image
            _, jpeg = cv2.imencode('.jpg', zoomed_img)

            # Convert the JPEG image to bytes and yield the result to the calling function
            yield jpeg.tobytes()

        # Release the camera resource when the loop finishes (though this part is never reached due to the infinite loop)
        camera.release()
