#include <Servo.h>
#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>

#define HAND 14         //Hand pin is D5
#define ARM 12          //ARM pin is D6
#define FINGERL 13      //FINGER Left pin is D7
#define FINGERR 15      //FINGER Right pin is D5
#define INPUT_BOX 5     //IR sensor pin is D1

enum STATE{
  STATE_START = 0,
  STATE_HAND0,            //Rising hand up
  STATE_ARM0,             //Rotating base to tower of product
  STATE_FINGER0,          //Attaching fingers to product box
  STATE_ARM1,             //Rotating base to Belt Conveyors
  STATE_HAND1,            //Lowering hand down
  STATE_FINGER1,          //Releasing product box
  STATE_STOP              //Back to idle state
};

// Create a servo object 
Servo servoMotorHand;
Servo servoMotorArm;
Servo servoMotorFingerL;
Servo servoMotorFingerR;

unsigned long previousMillis = 0;
const long interval = 1000;
int ledState = LOW;

int dir = 1;

//WIFI credential information
const char* ssid = "CC";
const char* password = "moddum5555";

//Creating UDP Listener Object. 
WiFiUDP UDPServer;
unsigned int UDPPort = 4210;

//Buffer to store incoming UDP packets
byte packetBuffer[8];

//State management
int reqState = STATE_STOP;        
int myState = STATE_STOP;         //currently state

//For test only
bool test = true;

int angle = 90;             //Angle of ARM when state STOP
int inputBoxDetect = 0;     //Default value for IR sersor 

const int FINGER_ANGLE_R = 30;    //Angle of Finger left when state STOP
const int FINGER_ANGLE_L = 0;     //Angle of Finger right when state STOP
//IN Real situation it have a problem with hardware, So 180 Degree in software is 90 degres on real product
const int ARM_ANGLE = 180;        //Angle of Arm when state STOP
const int HAND_ANGLE = 150;       //Angle of Finger left when state START  

void setup() { 
  //Attach each servoMotor to pin and initial angle to them
  servoMotorHand.attach(HAND);  
  servoMotorHand.write(0);

  servoMotorArm.attach(ARM);
  servoMotorArm.write(ARM_ANGLE);

  servoMotorFingerL.attach(FINGERL);
  servoMotorFingerL.write(FINGER_ANGLE_L);

  servoMotorFingerR.attach(FINGERR);
  servoMotorFingerR.write(FINGER_ANGLE_R);

  //Set other I/O pins
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(INPUT_BOX, INPUT_PULLUP);

  //Start WiFi connection
  WiFi.begin(ssid, password);
  Serial.begin(9600);
  Serial.println("");

  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Connected to ");
  Serial.println(ssid);
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // Start UDP server
  UDPServer.begin(UDPPort); 
}


void loop() {
  //Blink LED on NODEMCU for signal to know that NODEMCU is "Ready to operational"
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;    
    if (ledState == LOW)
      ledState = HIGH;  // Note that this switches the LED *off*
    else
      ledState = LOW;   // Note that this switches the LED *on*
    digitalWrite(LED_BUILTIN, ledState);
  }

  //Handle incoming UDP packets
  processPostData();

  //------------TESTING------------
  if(test){
    myState=STATE_START;
    test = false;
  }
  //------------TESTING------------

  //Handle state machine
  actuatorControl();
  delay(10);
}

void actuatorControl(){
  if(myState==STATE_START){

    //When STATE_START then change state to STATE_HAND0
    myState = STATE_HAND0;     

  }else if(myState==STATE_HAND0){ 

    //When STATE_HAND0 then rising hand up
    servoMotorHand.attach(HAND);
    servoMotorHand.write(HAND_ANGLE);
    delay(500);

    //Change state to STATE_ARM0
    myState = STATE_ARM0;

  }else if(myState==STATE_ARM0){

    //When STATE_ARM0 then rotating base to tower of product
    if(ARM_ANGLE >= angle){

      //Rotate base to tower of product by 10 degree per step(50ms)
      angle += 10;
      servoMotorArm.write(ARM_ANGLE-angle);
      delay(50);

    }else{

      //If ARM already rotate then set angle to 0 and change state to STATE_HAND1
      angle = 0;
      myState = STATE_HAND1;

    }
  }else if(myState==STATE_HAND1){

    //When STATE_HAND0 then lowering hand down
    servoMotorHand.write(0);
    delay(1000);

    //Change state to STATE_FINGER0
    myState = STATE_FINGER0;

  }else if(myState==STATE_FINGER0){
    delay(1000);

    //If IR sensor detect product box in front of hand
    if(digitalRead(INPUT_BOX)==LOW){

      //Attach fingers to product box
      servoMotorFingerL.write(10);
      servoMotorFingerR.write(20);
      delay(100);
      servoMotorFingerL.write(20);
      servoMotorFingerR.write(10);
      delay(100);
      servoMotorFingerL.write(30);
      servoMotorFingerR.write(0);
      delay(600);

      //Change state to STATE_ARM1
      myState = STATE_ARM1;
    }

  }else if(myState==STATE_ARM1){

    //When STATE_ARM1 then rotating base to Belt Conveyors with product box
    if(angle <= ARM_ANGLE){
      angle = 181;
      servoMotorArm.write(angle);
      delay(50);
    }else{

      //If base already rotate then set angle to 0 and change state to STATE_FINGER1
      angle = 0;
      myState = STATE_FINGER1;
      delay(500);
    }
  }else if(myState==STATE_FINGER1){

    //When STATE_FINGER1 then releasing product box
    delay(800);
    servoMotorFingerL.write(20);
    servoMotorFingerR.write(10);
    delay(100);
    servoMotorFingerL.write(10);
    servoMotorFingerR.write(20);
    delay(100);
    servoMotorFingerL.write(0);
    servoMotorFingerR.write(30);

    //Change state to STATE_STOP
    myState = STATE_STOP;

  }else if(myState==STATE_STOP){
    //When STATE_STOP then back to idle state

    //If received new state from server, update the state accordingly
    if(reqState==STATE_START){
      myState=STATE_START;
      reqState=STATE_STOP;
    }

    //Reset servos to initial positions
    servoMotorHand.attach(HAND);
    servoMotorHand.write(0);

    servoMotorArm.attach(ARM);
    servoMotorArm.write(ARM_ANGLE);

    servoMotorFingerL.attach(FINGERL);
    servoMotorFingerL.write(FINGER_ANGLE_L);

    servoMotorFingerR.attach(FINGERR);
    servoMotorFingerR.write(FINGER_ANGLE_R);
  }
  if(myState!=STATE_STOP){
    Serial.println(myState);
    Serial.println(digitalRead(INPUT_BOX));
  }
}

void processPostData(){
  // Check if a packet has been received from a client
  int cb = UDPServer.parsePacket();

  // If a packet was received, parse it and react accordingly
  if (cb) {

    // Reset the buffer to zero before reading new data in
    for(int i=0; i < sizeof(packetBuffer); i++){
      packetBuffer[i] = 0;
    }

    // Read the incoming data and print it out
    UDPServer.read(packetBuffer, sizeof(packetBuffer));

    // Convert the received data from byte array to string for easier processing and 
    // comparison with expected values or strings.  
    String data = String((const char*)packetBuffer);
    Serial.println(data);

    // Check if the received data matches the expected values or strings
    if(data.equals("START")){
      reqState = STATE_START;
    }else if(data.equals("STOP")){
      myState = STATE_STOP;
    }
  }
}
