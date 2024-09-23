import threading  # For creating a separate thread for capturing camera frames
import time  # For handling time-related operations like delays and timestamps

class BaseCamera:
    # Static class attributes
    thread = None  # This will hold the background thread that reads frames from the camera
    frame = None  # This will hold the current frame being captured by the camera
    last_access = 0  # Timestamp for the last time a client accessed the camera

    def __init__(self):
        """
        Constructor to initialize the camera object.
        This starts the background thread to read frames from the camera if it's not already started.
        """
        if BaseCamera.thread is None:
            # Record the last access time when the object is created
            BaseCamera.last_access = time.time()

            # Start the background frame capture thread
            BaseCamera.thread = threading.Thread(target=self._thread)
            BaseCamera.thread.start()

            # Wait until a frame is available before returning
            while self.get_frame() is None:
                time.sleep(0)  # Yield control to other threads

    def get_frame(self):
        """
        Return the current frame from the camera.
        Updates the last access time to indicate the camera is still being accessed.
        """
        # Update the last access time to the current time
        BaseCamera.last_access = time.time()

        # Return the latest frame captured by the background thread
        return BaseCamera.frame

    @staticmethod
    def frames():
        """
        A generator function that is meant to yield frames from the camera.
        This method must be implemented by subclasses because the base class
        does not know how to access camera frames.
        """
        raise RuntimeError('Must be implemented by subclasses.')

    def _thread(self):
        """
        Background thread for continuously capturing frames from the camera.
        This method runs in a separate thread and keeps fetching frames until
        there are no clients for 10 seconds.
        """
        print('Starting camera thread.')

        # Get the frames iterator from the subclass that implements the frames() method
        frames_iterator = self.frames()

        # Continuously fetch frames from the iterator
        for frame in frames_iterator:
            BaseCamera.frame = frame  # Update the current frame

            # If no clients have accessed the camera for more than 10 seconds, stop the thread
            if time.time() - BaseCamera.last_access > 10:
                frames_iterator.close()  # Close the frame generator
                print('Stopping camera thread due to inactivity.')
                break

        # Once the thread stops, set the thread attribute to None
        BaseCamera.thread = None
