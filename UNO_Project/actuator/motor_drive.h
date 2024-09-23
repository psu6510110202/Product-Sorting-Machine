//Define pins for controlling the motor via L293n
int motorEnablePin = 5;
int motorPin1 = 6;  
int motorPin2 = 7;  

//Running the motor
void motorRun()
{
  digitalWrite(motorPin1,HIGH);
  digitalWrite(motorPin2,LOW);
}

//Setting the motor speed with PWM and Running the motor
void motorSetSpeed(uint8_t pwm) 
{
  analogWrite(motorEnablePin,pwm);
  digitalWrite(motorPin1,HIGH);
  digitalWrite(motorPin2,LOW);
}

//Stopping the motor
void motorStop() 
{
  digitalWrite(motorPin1,LOW);
  digitalWrite(motorPin2,LOW);
}

//Setting the pin modes for the motor on L293N
void set_MotorPin()
{
  pinMode(motorPin1, OUTPUT);
  pinMode(motorPin2, OUTPUT);
  pinMode(motorEnablePin,OUTPUT);
}
