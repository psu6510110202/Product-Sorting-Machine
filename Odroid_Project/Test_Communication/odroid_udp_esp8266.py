import socket
from time import sleep

# Configuration
UDP_IP = "192.168.181.164"  # IP address of the ESP8266 NodeMCU
UDP_PORT = 4210           # Port number on which ESP8266 is listening

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
server_address = (UDP_IP, UDP_PORT)

# Message to send
message = "Hello from Odroid C4!"

try:
    while True:
        # Send message to ESP8266
        sock.sendto(b"START", server_address)
        print(f"Sent: {message} to {UDP_IP}:{UDP_PORT}")
        sleep(5)  # Wait for 1 second before sending next message
except KeyboardInterrupt:
    print("Exiting...")
finally:
    sock.close()  # Close the socket when done