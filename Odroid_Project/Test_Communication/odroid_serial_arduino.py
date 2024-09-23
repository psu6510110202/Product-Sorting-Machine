import serial
import time

# Set up serial communication
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # Update '/dev/ttyUSB0' to your specific port
ser.flush()

try:
    while True:
        # Send data to Arduino
        command = input("Command : ").strip()
        ser.write(f"{command}").encode()  # Send a message to Arduino
        print(f"Sent: {command} to Arduino")
        
        time.sleep(1)  # Wait for Arduino to process or respond

        # Read response from Arduino
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').rstrip()  # Read and decode response
            print(f"Arduino says: {response}")
        time.sleep(2)
except KeyboardInterrupt:
    print("Exiting")
finally:
    ser.close()  # Ensure the serial connection is closed on exit
