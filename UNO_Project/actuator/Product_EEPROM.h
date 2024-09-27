//Initial address and value of accessing EEPROM
uint16_t addr = 0;
uint8_t value = 0;      

unsigned char EEPROM_read1byte(uint16_t addr)  //ชื่อฟังก์ชันและพารามิเตอร์รับเข้า
{       
  while (EECR & (1<<EEPE)) ;                   //วนซ้ำจนกว่าบิต EEPE จะเปลี่ยนเป็นตรรกะต่ำ
  EEAR = addr;                                //คัดลอกพารามิเตอร์รับเข้าสู่เรจิสเตอร์ EEAR
  EECR |= (1<<EERE);                          //สั่งให้บิต EERE เป็นตรรกะสูงเพื่อเริ่มการอ่าน
  return EEDR;                                //นำค่าที่ปรากฏใน EEDR ไปใช้งาน
}

void EEPROM_Erase_and_Write1B(uint16_t addr, uint8_t data)
{
  while(EECR & (1<<EEPE)) ;   //วนซ้ำจนกว่าบิต EEPE จะเปลี่ยนเป็นตรรกะต่ำ
  EECR = 0x00;                //mode erase and write
  EEAR = addr;                //คัดลอกพารามิเตอร์รับเข้า addr สู่เรจิสเตอร์ EEAR
  EEDR = data;                //คัดลอกพารามิเตอร์รับเข้า data สู่เรจิสเตอร์ EEDR
  char backupSREG;            //ตัวแปรสำหรับเก็บค่าสถานะของเรจิสเตอร์ตัวบ่งชี้
  backupSREG = SREG;          //คัดลอกค่าในเรจิสเตอร์ตัวบ่งชี้ใส่ในตัวแปรที่ตั้งไว้
  cli();                      //ปิดทางการขัดจังหวะส่วนกลางของตัวประมวลผล
  EECR |= (1<<EEMPE);         //สั่งให้บิต EEMPE ใน EECR เป็นตรรกะสูง
  EECR |= (1<<EEPE);          //สั่งให้บิต EEPE ใน EECR เป็นตรรกะสูง
  SREG = backupSREG;          //คืนค่าเรจิสเตอร์ตัวบ่งชี้กลับสู่สถานะเดิม
}

void EEPROM_Erase_only(uint16_t addr)
{  
  while(EECR & (1<<EEPE)) ;   //วนซ้ำจนกว่าบิต EEPE จะเปลี่ยนเป็นตรรกะต่ำ
  EECR = 0b01 << EEPM0;       //ลบอย่างเดียว 
  EEAR = addr;                //คัดลอกพารามิเตอร์รับเข้า addr สู่เรจิสเตอร์ EEAR
  EEDR = 0xFF;                //คัดลอกพารามิเตอร์รับเข้า data สู่เรจิสเตอร์ EEDR
  char backupSREG;            //ตัวแปรสำหรับเก็บค่าสถานะของเรจิสเตอร์ตัวบ่งชี้
  backupSREG = SREG;          //คัดลอกค่าในเรจิสเตอร์ตัวบ่งชี้ใส่ในตัวแปรที่ตั้งไว้
  cli();                      //ปิดทางการขัดจังหวะส่วนกลางของตัวประมวลผล
  EECR |= (1<<EEMPE);         //สั่งให้บิต EEMPE ใน EECR เป็นตรรกะสูง
  EECR |= (1<<EEPE);          //สั่งให้บิต EEPE ใน EECR เป็นตรรกะสูง
  SREG = backupSREG;          //คืนค่าเรจิสเตอร์ตัวบ่งชี้กลับสู่สถานะเดิม
}

//Function to scan and find the first non-zero value in the EEPROM
uint16_t scan_EEPROM()
{
  int i;
  uint8_t d;

  //Scan through the entire memory space of the EEPROM and find the first non-zero value
  for(i = 0; i < 1024; i++)
  {
    d = EEPROM_read1byte(i);      //Read data 1 Byte from specified Memory 
    if(d != 0xFF)                 
    {
      //If non-zero value is found, store its address and value in global variables and return the address
      addr = i;
      value = d;

    }
  }
}

//Function to read a byte from the specified memory address
uint8_t setup_EEPROM(){
  scan_EEPROM();
  return value;
}

//Function to erase and write new data to the next memory
void save_NewProductCount(uint8_t productCount){
  EEPROM_Erase_only(addr);
  EEPROM_Erase_and_Write1B(addr+1, productCount);
}