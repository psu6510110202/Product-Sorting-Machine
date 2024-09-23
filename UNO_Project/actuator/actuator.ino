#include <Servo.h>
#include <AFMotor.h>
#include <ArduinoSTL.h>
#include "motor_drive.h"     //Control DC Motor
#include "Controlkeypad.h"   //Control LCD Display, Keypad 
#include "ControlTm1638.h"   //Control TM1638 Display Up time
#include <avr/wdt.h>         //Control watchdog timer
#include "Product_EEPROM.h"  //Control EEPROM of Arduino

#define DEBUG

// Declare the Servo pin 
int servoPinHorizon = A3;

// Create a servo object 
Servo servoHorizon ;

//Init the servo speed PWM
int dcMotorPWMVal = 255;

//Declare the IR sensor pin
int inputPinInspect = 2;              //Used for stop belt conveyor when detect product box
int inputPinSort = 3;                 //Used for adjust for servo direction before product falling

// Define the state of the IR sensors
int inputPinInspectState = HIGH;
int inputPinInspectStatePre = HIGH;
int inputPinSortState = HIGH;
int inputPinSortStatePre = HIGH;

//Define the state of sorting to prevent ghost sensors
int productAlreadyClassification = LOW;

//Initial variables values
int productType = 0; 
int systemState = 0;
bool doSort = false;
long prev_time;

//Mock the product count values before get from EEPROM
int productCount = -1;

//Create vectors for easier addition and removal of elements
std::vector<int> vProductType;

//List All state in system
enum STATE {
  STATE_STOP = 0,
  STATE_RUN,            //Running belt conveyors 
  STATE_PAUSE,          //Pause belt conveyors to classify product box
  STATE_DETECTED,       //Product box is detected and already processed
  STATE_TEST            //Not used anymore
};

void setup() {
  Serial.begin(9600);

  //Setup Motor pins
  set_MotorPin();

  //Setup LCD and Keypad
  set_LCD_Keypad();

  //Setup TM1638 pin and connection
  setup_TM1638();
  productCount = setup_EEPROM();
  
  //Enable watch dog timer at 8 seconds
  wdt_enable(WDTO_8S);

  //Setup IR sensor and LED pins
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(inputPinInspect, INPUT);
  pinMode(inputPinSort, INPUT);

  //Setup Servo motor
  servoHorizon.attach(servoPinHorizon);
  servoHorizon.write(60);

  //Attach interrupt for IR sensors
  attachInterrupt(digitalPinToInterrupt(inputPinInspect), readInspectPin, CHANGE);
  attachInterrupt(digitalPinToInterrupt(inputPinSort), readSortPin, CHANGE);
}

void loop() {
  //Reset watchdog timer each loop
  wdt_reset();

  //Read Serial input to control system
  if (Serial.available()) {

    //Read incoming data from Serial
    String data = Serial.readString();
    Serial.println(data);

    if(data.indexOf("OFF")!=-1){

      //If incoming data is OFF then stop belt conveyor 
      systemState = STATE_STOP;
      vProductType.clear();           //Clear the product type vector
      servoHorizon.write(45);         //Reset the servo to 45 degrees

    }else if(data.indexOf("RUN")!=-1){

      //If incoming data is RUN then start belt conveyors
      //Set system state to STATE_RUN
      systemState = STATE_RUN;

      //Calling getValue function to extract motor PWM from full data
      dcMotorPWMVal = getValue(data, ':', 1).toInt();
      Serial.println(dcMotorPWMVal);

      //Set the motor speed using motorSetSpeed function with dcMotorPWNVal
      motorSetSpeed(dcMotorPWMVal);

    }else if(data.indexOf("TEST")!=-1){

      //Test working of Sorting servo motor
      //Set system state to STATE_TEST
      systemState = STATE_TEST;
      int testServo = getValue(data, ':', 1).toInt();
      Serial.println(testServo);
      servoHorizon.write(testServo);

    }else if(data.indexOf("Detected")!=-1){

      //If incoming data is Detected then record the product type
      productType = getValue(data, ':', 1).toInt();

      //Add product type to end of vector
      vProductType.push_back(productType);

      //Set system state to STATE_DETECTED
      systemState = STATE_DETECTED;
    }
  }

  //Check if system state is STATE_RUN and product box is detected
  if(systemState==STATE_RUN){
    
    // If the IR sensor detects a product and it was not detecting it just a moment ago
    if(inputPinInspectState==LOW&&inputPinInspectStatePre==HIGH){

      //Set system state to STATE_PAUSE to pause belt conveyor 
      systemState=STATE_PAUSE;

    }else{
      //If the IR sensor is not detected then run the motor
      motorRun();
    }
  }else if(systemState==STATE_PAUSE){
    //When system state is STATE_PAUSE then stop the motors
    motorStop();

    //Send command to Odroid for starting classification
    Serial.println("STATE_PAUSE");

    //Set system state to STATE_STOP for waiting classification process
    systemState = STATE_STOP;
  }else if(systemState==STATE_STOP){
    
    //When system state is STATE_STOP then stop the motors
    motorStop();

  }else if(systemState==STATE_TEST){
    //Noting to do anymore for testing purposes
  }else if(systemState==STATE_DETECTED){

    //When system state is STATE_DETECTED then 
    //send command to Odroid for starting belt conveyor again
    Serial.println("STATE_DETECTED");

    //Set system state to STATE_STOP for waiting RUN command from Odroid
    systemState = STATE_STOP;

    //Set productAlreadyClassification to HIGH to enable sort IR sensor
    productAlreadyClassification = HIGH;
  }

  //Set state of IR sensor to prevent multiple detection in same time 
  inputPinInspectStatePre = inputPinInspectState;

  //Control Sorting servo to change direction of product falling
  controlServos();

  //Update LCD display with current product count and standby time
  LCD_Display(productCount);
  display_StandbyTime();

  delay(10);
}

//Interrupt function of the IR sensor for stop belt coveyor to classify product
void readInspectPin(){
  inputPinInspectState = digitalRead(inputPinInspect);
}

//Interrupt function of the IR sensor for adjusting for servo direction before product falling
void readSortPin(){
  inputPinSortState = digitalRead(inputPinSort);
}

//Control Sorting servo to change direction of product falling
void controlServos(){

  //If the IR sensor detects a product and it was not detecting it just a moment ago
  if(inputPinSortStatePre==HIGH&&inputPinSortState==LOW){

    //Set doSort to true to start sorting process
    doSort = true;  

    //If product already classification, then update product count and save to EEPROM
    if(productAlreadyClassification==HIGH){
      productCount += 1;
      save_NewProductCount(productCount);
      productAlreadyClassification = LOW;   //Reset productAlreadyClassification
    }
  }

  //Set state of IR sensor to prevent multiple detection in same time
  inputPinSortStatePre = inputPinSortState;
  
  //Start sorting process when doSort is true
  if(doSort){

    //Set doSort back to false
    doSort = false;

    //If the ProductType vector is not empty
    if(vProductType.size()>0){
      productType = vProductType[0];              //Set productType back to first index of productType vector
      vProductType.erase(vProductType.begin());   //Remove first element of productType vector
      Serial.println(productType);        
    }

    //Control servo to change direction of product falling base on productType
    switch (productType)
    {
      case 0:
        servoHorizon.write(60);     //Butcher Premium
        break;
      case 1:
        servoHorizon.write(100);    //Butcher Normal
        break;
      case 2:
        servoHorizon.write(140);    //Butcher Shop
        break;
      default:
        break;
    }
  }
}

String getValue(String data, char separator, int index) {
    int found = 0;                                          // Counter for how many segments have been found.
    int strIndex[] = { 0, -1 };                             // Stores the start and end indices of the current segment.
    int maxIndex = data.length() - 1;                       // Maximum index of the string.

    for (int i = 0; i <= maxIndex && found <= index; i++) { // Loop through the string.
        if (data.charAt(i) == separator || i == maxIndex) { // Check for separator or end of string.
            found++;                                        // Increment the segment counter.
            strIndex[0] = strIndex[1] + 1;                  // Update start index to be one position after last end.
            strIndex[1] = (i == maxIndex) ? i + 1 : i;      // Update end index, accounting for last character.
        }
    }

    // If the desired index was found, return the substring. Otherwise, return an empty string.
    return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}
