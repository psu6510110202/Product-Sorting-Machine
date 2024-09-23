#include <ESP8266WiFi.h>
#include <WiFiUdp.h>

const char* ssid = "CC";        // Your WiFi network name
const char* password = "moddum5555";  // Your WiFi network password
long previous_time;
byte packetBuffer[8];

WiFiUDP udp;
unsigned int localPort = 4210;  // Local port to listen for UDP packets

void setup() {
  Serial.begin(9600);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi!");

  // Start UDP
  udp.begin(localPort);
  previous_time = 0;
}

void loop() {
  int packetSize = udp.parsePacket();
  if(millis() - previous_time > 10000){
    Serial.printf("UDP listening on IP: %s, Port: %d\n", WiFi.localIP().toString().c_str(), localPort);
    previous_time = millis();
  }
  if (packetSize) {
    // Read incoming UDP packet
    for(int i=0; i < sizeof(packetBuffer); i++){
      packetBuffer[i] = 0;
    }
    udp.read(packetBuffer, sizeof(packetBuffer));
    String data = String((const char*)packetBuffer);
    // if (data.equals("START")) {
    //   Serial.println("Confirm Communication");
    // } else {
    Serial.printf("Received: %s\n", data);  // Print received data to Serial
    // }
  }
}
