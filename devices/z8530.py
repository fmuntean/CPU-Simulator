# AMD Z8530  (Asynchronous Communication) simulator


class UART:
    def __init__(self, base):
        self.baseAddr = base

        #it has 16 write registers 
        self.WRS = [0] * 16
        self.RRS = [0] * 16

        self.RRS[0] = 0b00000100

        self.rx = 0 # byte received
        self.tx = 0 # byte to transmit

        
    def match(self,addr):
        if (addr>=self.baseAddr and addr<=self.baseAddr+4):
            return True
        return False

    #read internal register 
    def read(self,addr):
      channel = (addr & 0x02)>>1
      cmd_data = addr & 0x01

      ret = 0
      if channel==1 and cmd_data==0: # channel A cmd
        index = self.WRS[0]
        ret = self.RRS[index]
        if index>0:
           self.WRS[0] = 0
      elif channel==1 and cmd_data==1: #channel A Data
          ret = self.rx
          self.rx=0
          self.RRS[0] = self.RRS[0] & 0b11111110

      return ret
      pass

    #write internal registers
    def write(self,addr, val):
      channel = (addr & 0x02)>>1
      cmd_data = addr & 0x01

      if channel==1 and cmd_data==0: # channel A cmd
        index = self.WRS[0]
        self.WRS[index] = val
        if index>0:
           self.WRS[0] = 0
      elif channel==1 and cmd_data==1: #channel A Data
          self.tx = val
          self.RRS[0] = self.RRS[0] & 0b11111011
          
      pass

    #used to receive data from outside world
    def receive(self, data):
        self.rx = data
        self.RRS[0] = self.RRS[0] | 0b00000001
        pass
        
    #used to transmit data to outside world
    def transmit(self):
        if self.RRS[0] & 0b00000100:
           return -1
        
        ret = self.tx
        self.tx=0
        self.RRS[0] = self.RRS[0] | 0b00000100
        return ret