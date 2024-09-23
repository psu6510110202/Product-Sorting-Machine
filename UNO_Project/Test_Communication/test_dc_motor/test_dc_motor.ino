int in1 = 6;
int in2 = 7;
int enA = 5;

void setup() {
  Serial.begin(9600);
  pinMode(enA, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
}

void motorOFF(){
  analogWrite(enA, 255);
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
}

void motorRUN(){
  analogWrite(enA, 255);
  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
}

void loop() {
  // if(Serial.available()){
  //   String data = Serial.readString();
  //   if(data.indexOf("OFF") != -1){
  //     motorOFF();
  //   }
  //   else if(data.indexOf("RUN") != -1){
  //     motorRUN();
  //   }
  // }
  motorRUN();

}

