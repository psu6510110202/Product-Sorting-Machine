#include <Servo.h>
Servo myservo; //ประกาศตัวแปรแทน Servo กำหนดข
void setup()
{
  myservo.attach(A3); // กำหนดขา 9 ควบคุม Servo
}
void loop()
{
  myservo.write(45); // สั่งให้ Servo หมุนไปองศาที่ 0
  delay(1000); // หน่วงเวลา 1000ms
  myservo.write(90); // สั่งให้ Servo หมุนไปองศาที่ 90
  delay(1000); // หน่วงเวลา 1000ms
  myservo.write(135); // สั่งให้ Servo หมุนไปองศาที่ 180
  delay(1000); // หน่วงเวลา 1000ms
}