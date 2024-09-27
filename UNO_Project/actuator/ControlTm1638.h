//define pin for communication with TM1638
const int strobe = 11;     
const int clock = 12;  
const int data = 13;   

int hour_tm, minute_tm, sec_tm;
long prev_time_tm1638;

//Used for send Commands to TM1638
void sendCommand(uint8_t value)
{
  digitalWrite(strobe, LOW);                  //Tell TM1638, Command is outgoing
  shiftOut(data, clock, LSBFIRST, value);     //Shift out data to TM1638 with LSBFIRST
  digitalWrite(strobe, HIGH);                 //Tell TM1638, No more Data/Command 
}

//Used for turn off all light device on TM1638
void reset()
{
  sendCommand(0x40);                          //Set auto address increment mode
  digitalWrite(strobe, LOW);                  //Tell TM1638, Start Address is outgoing
  shiftOut(data, clock, LSBFIRST, 0xc0);      //Set starting address to C0
  for(uint8_t i = 0; i < 16; i++)             //Address of 8 7Segment and 8 LED
  {
    shiftOut(data, clock, LSBFIRST, 0x00);    //Shift data to turn off 7Segment and LED
  }
  digitalWrite(strobe, HIGH);                 //Tell TM1638, No more Data/Command 
}

//Setup connection for TM1638
void setup_TM1638()
{
  //Setup pin configuration to communicate with TM1638
  pinMode(strobe, OUTPUT);  
  pinMode(clock, OUTPUT);   
  pinMode(data, OUTPUT);   

  hour_tm = 0;
  minute_tm = 0;
  sec_tm = 0;

  sendCommand(0x8f);    //Send command to make TM1638 start working
  reset();              //turn off all light device on TM1638
}

//Update time on TM1638 display
void update_time(){
  if(sec_tm == 59){                   
    sec_tm = 0;                        //if seconds is equal to 59 it can't more increment, Reset to 0
    if(minute_tm == 59){               
      minute_tm = 0;                   //if minutes is equal to 59 it can't more increment, Reset to 0
      hour_tm == 23 ? 0 : hour_tm++;  //if hours is equal to 23 it can't more increment, Reset to 0
                                      //But if it < 23 then increment by 1 every 60 minutes
    }
    else{
      minute_tm++;                      //Increment minutes by 1 every 60 seconds
    }
  }
  else{
    sec_tm++;                           //Increment the seconds by 1 every 1 seconds
  }
}

void display_7seg()
{
  //Set output pattern for display digits 0 - 9
  uint8_t digits[] = { 0x3f, 0x06, 0x5b, 0x4f, 0x66, 0x6d, 0x7d, 0x07, 0x7f, 0x6f };

  sendCommand(0x44);                                    //Set single address mode to specified by user

  //Display hour 2 digit on TM1638
  digitalWrite(strobe, LOW);                            //Tell TM1638, data is outgoing
  shiftOut(data, clock, LSBFIRST, 0xc0);                //Shift out address 0xC0 (First 7-Segment) to TM1638
  shiftOut(data, clock, LSBFIRST, digits[hour_tm/10]);  //Shift out data hour digit ten to TM1638  
  digitalWrite(strobe, HIGH);                           //Tell TM1638, No more Data/Command 
  digitalWrite(strobe, LOW);                            //Tell TM1638, data is outgoing
  shiftOut(data, clock, LSBFIRST, 0xc2);                //Shift out address 0xC2 (Second 7-Segment) to TM1638
  shiftOut(data, clock, LSBFIRST, digits[hour_tm%10]);  //Shift out data hour digit one to TM1638
  digitalWrite(strobe, HIGH);                           //Tell TM1638, No more Data/Command

  //Display separator between hour and minute
  digitalWrite(strobe, LOW);        
  shiftOut(data, clock, LSBFIRST, 0xc4);                //Shift out address 0xC4 (Third 7-Segment) to TM1638
  shiftOut(data, clock, LSBFIRST, 0x40);                //Shift out data symbol "-"  TM1638  
  digitalWrite(strobe, HIGH);

  //Display minute 2 digit on TM1638
  digitalWrite(strobe, LOW);
  shiftOut(data, clock, LSBFIRST, 0xc6);                //Shift out address 0xC6 (Fourth 7-Segment) to TM1638
  shiftOut(data, clock, LSBFIRST, digits[minute_tm/10]);//Shift out data minute digit ten to TM1638  
  digitalWrite(strobe, HIGH);
  digitalWrite(strobe, LOW);
  shiftOut(data, clock, LSBFIRST, 0xc8);                //Shift out address 0xC8 (Fifth 7-Segment) to TM1638
  shiftOut(data, clock, LSBFIRST, digits[minute_tm%10]);//Shift out data minute digit one to TM1638 
  digitalWrite(strobe, HIGH);

  //Display separator between minute and seconds
  digitalWrite(strobe, LOW);  
  shiftOut(data, clock, LSBFIRST, 0xca);                //Shift out address 0xCA (Sixth 7-Segment) to TM1638
  shiftOut(data, clock, LSBFIRST, 0x40);                //Shift out data symbol "-"  TM1638  
  digitalWrite(strobe, HIGH);

  //Display seconds 2 digit on TM1638
  digitalWrite(strobe, LOW);
  shiftOut(data, clock, LSBFIRST, 0xcc);               //Shift out address 0xCC (Seventh 7-Segment) to TM1638
  shiftOut(data, clock, LSBFIRST, digits[sec_tm/10]);  //Shift out data seconds digit ten to TM1638  
  digitalWrite(strobe, HIGH);
  digitalWrite(strobe, LOW);
  shiftOut(data, clock, LSBFIRST, 0xce);              //Shift out address 0xCC (Seventh 7-Segment) to TM1638
  shiftOut(data, clock, LSBFIRST, digits[sec_tm%10]); //Shift out data seconds digit one to TM1638  
  digitalWrite(strobe, HIGH);

}

//Display Stand by time or Up time of system to TM1638
void display_StandbyTime()
{
  display_7seg();
  if(millis() - prev_time_tm1638 > 1000){  
    update_time();
    prev_time_tm1638 = millis();
  }  
}