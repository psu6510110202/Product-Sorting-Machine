import time
import threading
try:
    from greenlet import getcurrent as get_ident    # Tries to import from 'greenlet' to get the current thread ID
except ImportError:
    try:
        from thread import get_ident                # Fallback to thread module if greenlet isn't available
    except ImportError:
        from _thread import get_ident               # Finally, use '_thread' for thread identification if other imports fail

# CameraEvent class to manage signaling for frame availability
class CameraEvent(object):
    """An Event-like class that signals all active clients when a new frame is available."""
    
    def __init__(self):
        self.events = {}                             # Dictionary to store event objects and timestamps for each client

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()                         # Get the current thread/client identifier
        if ident not in self.events:
            # New client detected, create a new event and add it to the events dict
            # The event has two parts: threading.Event() and the time the event was last updated
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()         # Wait until the event is set (indicating a new frame)

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        now = time.time()                           # Get the current time
        remove = None
        # Iterate over each client to update the event state
        for ident, event in self.events.items():
            if not event[0].isSet():
                # If the event for this client is not set, set it (indicating a new frame)
                event[0].set()
                event[1] = now                      # Update the timestamp for this event
            else:
                # If the event is already set, the client may have missed the previous frame
                # If more than 5 seconds have passed since the last update, assume the client is gone
                if now - event[1] > 5:
                    remove = ident                  # Mark this client for removal
        if remove:
            del self.events[remove]                 # Remove the inactive client

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()         # Clear the event, signaling that the frame was processed

# BaseCamera class to handle capturing frames in the background and serving them to clients
class BaseCamera(object):
    thread = None                               # Background thread that reads frames from the camera
    frame = None                                # Current frame is stored here
    last_access = 0                             # Last time a client accessed a frame
    event = CameraEvent()                       # Event signaling system for frame availability

    def __init__(self):
        """Start the background camera thread if it isn't running yet."""
        if BaseCamera.thread is None:
            BaseCamera.last_access = time.time()  # Update last access time to the current time

            # Start the background frame reading thread
            BaseCamera.thread = threading.Thread(target=self._thread)
            BaseCamera.thread.start()

            # Wait until frames are available
            while self.get_frame() is None:
                time.sleep(0)                   # Small sleep to avoid busy-waiting

    def get_frame(self):
        """Return the current camera frame."""
        BaseCamera.last_access = time.time()    # Update last access time

        # Wait for the camera thread to signal that a new frame is available
        BaseCamera.event.wait()
        BaseCamera.event.clear()                # Clear the event once the frame has been processed

        return BaseCamera.frame                 # Return the current frame

    @staticmethod
    def frames():
        """"Generator that returns frames from the camera."""
        raise RuntimeError('Must be implemented by subclasses.')  # This function should be implemented by a subclass

    @classmethod
    def _thread(cls):
        """Camera background thread that continuously reads frames."""
        print('Starting camera thread.')
        frames_iterator = cls.frames()      # Get the frame generator

        for frame in frames_iterator:
            BaseCamera.frame = frame        # Store the latest frame
            BaseCamera.event.set()          # Signal clients that a new frame is available
            time.sleep(0)                   # Yield execution to other threads

            # Stop the thread if no client has requested a frame in the last 10 seconds
            if time.time() - BaseCamera.last_access > 10:
                frames_iterator.close()     # Close the frame generator to stop reading frames
                print('Stopping camera thread due to inactivity.')
                break

        BaseCamera.thread = None            # Reset the thread to None once it has stopped
