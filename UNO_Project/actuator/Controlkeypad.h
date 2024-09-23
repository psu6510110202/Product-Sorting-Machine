#include <LiquidCrystal_I2C.h>
#include <Keypad_I2C.h> //นำ KEYPAD มาใช้ในรูปแบบ I2C
#include <Keypad.h>
#include <Wire.h>
#include <TimeLib.h>  //TimeLibary 
#include <DS1307RTC.h>

#define I2CADDR 0x20  

//Setup ROWS and COLS detail for keypad 
const byte ROWS = 4;
const byte COLS = 4;
char hexaKeys[ROWS][COLS] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};

//Setup row and col pin to used with PCF8574
byte rowPins[ROWS] = {7, 6, 5, 4};
byte colPins[COLS] = {3, 2, 1, 0};

unsigned long last_time;
bool blink_txt;

//Initialize connection to peripheral device 
LiquidCrystal_I2C lcd(0x27, 16, 2); //Module IIC/I2C Interface บางรุ่นอาจจะใช้ N 0x3f
Keypad_I2C keypad(makeKeymap(hexaKeys), rowPins, colPins, ROWS, COLS, I2CADDR);
tmElements_t tm; 

int Hour, Minute;
int Year, Month, Day;
long previous_time;

//Print the value in format 2 digits
void print2digit(int val) {
  if (val < 10 && val >= 0)
    lcd.print(0);
  lcd.print(val);
}

//Erase and Write EEPROM at specified location with data
void EEPROM_erase_write(uint16_t addr, uint8_t data)
{
  while(EECR & (1<<EEPE)) ; //วนซ้ำจนกว่าบิต EEPE จะเปลี่ยนเป็นตรรกะต่ำ
  EECR = 0x00;      //mode erase and write
  EEAR = addr;      //คัดลอกพารามิเตอร์รับเข้า addr สู่เรจิสเตอร์ EEAR
  EEDR = data;      //คัดลอกพารามิเตอร์รับเข้า data สู่เรจิสเตอร์ EEDR
  char backupSREG;    //ตัวแปรสำหรับเก็บค่าสถานะของเรจิสเตอร์ตัวบ่งชี้
  backupSREG = SREG;    //คัดลอกค่าในเรจิสเตอร์ตัวบ่งชี้ใส่ในตัวแปรที่ตั้งไว้
  cli();        //ปิดทางการขัดจังหวะส่วนกลางของตัวประมวลผล
  EECR |= (1<<EEMPE);   //สั่งให้บิต EEMPE ใน EECR เป็นตรรกะสูง
  EECR |= (1<<EEPE);    //สั่งให้บิต EEPE ใน EECR เป็นตรรกะสูง
  SREG = backupSREG;    //คืนค่าเรจิสเตอร์ตัวบ่งชี้กลับสู่สถานะเดิม
}

//Erase EEPROM at specified location
void EEPROM_erase(uint16_t addr)
{  
  while(EECR & (1<<EEPE)) ; //วนซ้ำจนกว่าบิต EEPE จะเปลี่ยนเป็นตรรกะต่ำ
  EECR = 0b01 << EEPM0;   //ลบอย่างเดียว 
  EEAR = addr;      //คัดลอกพารามิเตอร์รับเข้า addr สู่เรจิสเตอร์ EEAR
  EEDR = 0xFF;      //คัดลอกพารามิเตอร์รับเข้า data สู่เรจิสเตอร์ EEDR
  char backupSREG;    //ตัวแปรสำหรับเก็บค่าสถานะของเรจิสเตอร์ตัวบ่งชี้
  backupSREG = SREG;    //คัดลอกค่าในเรจิสเตอร์ตัวบ่งชี้ใส่ในตัวแปรที่ตั้งไว้
  cli();        //ปิดทางการขัดจังหวะส่วนกลางของตัวประมวลผล
  EECR |= (1<<EEMPE);   //สั่งให้บิต EEMPE ใน EECR เป็นตรรกะสูง
  EECR |= (1<<EEPE);    //สั่งให้บิต EEPE ใน EECR เป็นตรรกะสูง
  SREG = backupSREG;    //คืนค่าเรจิสเตอร์ตัวบ่งชี้กลับสู่สถานะเดิม
}

//Erase all location in EEPROM
void EEPROM_erase_all()
{
  int i;
  for(i = 0; i < 1024; i++)
  {
    EEPROM_erase(i);
  }
}


unsigned int mode, digit, date;   //digit เอาไว้ check ว่ากดเลือก digit ไหน
bool displayAllProduct = false;  // ตัวแปรสถานะสำหรับการสลับโหมด

//Setup LCD and Keypad
void set_LCD_Keypad() {
  Wire.begin();
  keypad.begin();
  lcd.init();
  lcd.backlight();
  lcd.home();
  previous_time = 0;
  date = 0;
}

bool flag = false;        // ตรวจสอบว่ามีการแก้ไขหรือไม่
bool blink_tx = false;

//Display the DateTime and Product Count on LCD Screen
void LCD_Display(int value) {

  //Read datetime from EEPROM on DS1307
  if (RTC.read(tm)) {
    char key = keypad.getKey();               //Read keypad from PCF8574
    Serial.println(key);

    //Switch display screen between Datetime and Product count when pressed *
    if (key == '*') {
      displayAllProduct = !displayAllProduct;  
    }

    //Display Product count on LCD screen
    if (displayAllProduct) {
      if(millis() - previous_time > 500){
        lcd.clear();
        lcd.setCursor(1, 0);
        lcd.print("Product Count");
        lcd.setCursor(0, 1);
        lcd.print(value);
        lcd.setCursor(12, 1);
        lcd.print("Unit");
        previous_time = millis();
      }
    }

    //Next area is for Display datetime, If now is in product count mode then get back
    if (displayAllProduct) {
      return;  
    }

    //Display Datetime on LCD screen (Default mode)
    if (key == 'A') {

      //Enter Date editor mode when pressd A on keypad
      date < 3 ? date++ : date = 1;       //Switch to next unit (day, month, year) every time pressd A
      mode = 0;                           //Set mode to 0 for indicators Date Editor mode
      flag = true;                        //Set flag for editor mode (Second Ensuring for enter editor mode)

    } else if (key == 'B') {

      //Enter Date editor mode when pressd A on keypad
      digit = !digit;                     //Switch unit between hour and minute every time pressed B
      mode = 1;                           //Set mode to 1 for indicators Time editor mode
      flag = true;                        //Set flag for editor mode (Second Ensuring for enter editor mode)

    } else if (key == 'C') {
      
      //Increment value of current unit every time pressed C
      if (!mode) {

        //Increment Date unit based on date value
        if (date == 1)
          // Check the number of days in the current month
          if ((Month % 2) != 0) {
              Day < 31 ? Day++ : Day = 1;          // Odd months have 31 days
          } else if (Month == 2) {
              if ((Year % 4 == 0 && Year % 100 != 0) || (Year % 400 == 0)) {
                Day < 29 ? Day++ : Day = 1;         // Leap year, February has 29 days
              } else {
                Day < 28 ? Day++ : Day = 1;         // Non-leap year, February has 28 days
              }
          } else {
              Day < 30 ? Day++ : Day = 1;          // Even months have 30 days
          }
        else if (date == 2)
          Month < 12 ? Month++ : Month = 1;       //Increment month by 1 until more than 13 then reset to 1 
        else if (date == 3)
          Year < 2099 ? Year++ : Year = 1990;     //Increment year by 1 until more than 2099 then reset to 1990

      } else {

        //Increment time unit based on digit value
        if (!digit)
          Hour < 23 ? Hour++ : Hour = 0;        //Increment hour by 1 until more than 23 hour then reset to 0
        else
          Minute < 59 ? Minute++ : Minute = 0;  //Increment minute by 1 until more than 59 minutes then reset to 0
      }

    } else if (key == 'D') {

      //Decrement value of current unit every time pressed D
      if (!mode) {

        //Decrement Date unit based on date value
        if (date == 1)

          // Check the number of days in the previous month
          if ((Month % 2) != 0) {
              Day > 1 ? Day-- : Day = 31;   // Odd months (except February) have 31 days
          } else if (Month == 2) {
              if ((Year % 4 == 0 && Year % 100 != 0) || (Year % 400 == 0)) {
                  Day > 1 ? Day-- : Day = 29;  // Leap year
              } else {
                  Day > 1 ? Day-- : Day = 28;  // Non-leap year
              }
          } else {
              Day > 1 ? Day-- : Day = 30;  // Even months have 30 days
          }

        else if (date == 2)
          Month > 1 ? Month-- : Month = 12;   //Decrement month by 1 until less than 1 then reset to 12
        else if (date == 3)
          Year > 1 ? Year-- : Year = 2099;    //Decrement year by 1 until less than 1990 then reset to 2099
      } else {

        //Decrement time unit based on digit value
        if (!digit)
          Hour > 0 ? Hour-- : Hour = 23;        //Decrement hour by 1 until less than 0 hour then reset to 0
        else
          Minute > 0 ? Minute-- : Minute = 59;  //Decrement minute by 1 until less than 0 minute then reset to 0
      }

    } else if (key == '#') {

      // Save current datetime to RTC and reset date and flag
      tm.Day = Day;
      tm.Month = Month;
      tm.Year = CalendarYrToTm(Year);
      tm.Hour = Hour;
      tm.Minute = Minute;
      RTC.write(tm);
      date = 0;
      flag = false;

    } else if (key == '1') {

      // Clear all data in EEPROM and write 0 at location 0 when pressed 1 on keypad
      EEPROM_erase_all();
      EEPROM_erase_write(0, 0);
      delay(1000);
      
    }

    //Display Blink Date unit when in editor mode
    if(millis() - previous_time > 500){
      lcd.clear();
      previous_time = millis();
    }
    lcd.setCursor(0, 0);
    lcd.print("D/M/Y=");
    if (flag && mode == 0) {
      if ((millis() - last_time) > 1000) {
        blink_tx = !blink_tx;
        last_time = millis(); // อัพเดต last_time
      }
      if (date == 1) {

        //Blink Day
        blink_tx ? (void)lcd.print("  ") : print2digit(Day);
        lcd.print("/");
        print2digit(Month);
        lcd.print("/");
        lcd.print(Year);

      } else if (date == 2) {

        //Blink Month
        print2digit(Day);
        lcd.print("/");
        blink_tx ? (void)lcd.print("  ") : print2digit(Month);
        lcd.print("/");
        lcd.print(Year);

      } else if (date == 3) {

        //Blink Year
        print2digit(Day);
        lcd.print("/");
        print2digit(Month);
        lcd.print("/");
        blink_tx ? lcd.print("    ") : lcd.print(Year);

      }
    } else {
      
      //Display Date when Blink is disabled
      Day = tm.Day;
      Month = tm.Month;
      Year = tmYearToCalendar(tm.Year);
      lcd.print(Day);
      lcd.print("/");
      print2digit(Month);
      lcd.print("/");
      print2digit(Year);
    }

    //Display Blink Time unit when in editor mode
    lcd.setCursor(0, 1);
    lcd.print("Time = ");
    if (flag && mode == 1) {
      if ((millis() - last_time) > 1000) {
        blink_tx = !blink_tx;
        last_time = millis();  // อัพเดต last_time
      }
      if (!digit) {

        //Blink Hour
        blink_tx ? (void)(lcd.print("  ")) : print2digit(Hour);
        lcd.print(":");
        print2digit(Minute);
      } else {
        
        //Blink Minute
        print2digit(Hour);
        lcd.print(":");
        blink_tx ? (void)(lcd.print("  ")) : print2digit(Minute);
      }
    } else {

      //Display Time when Blink is disabled
      Hour = tm.Hour;
      Minute = tm.Minute;
      print2digit(Hour);
      lcd.print(":");
      print2digit(Minute);
    }
  }
}

