# ACIA (Asynchronous Communication) simulator

class UART:
    def __init__(self, base):
        self.baseAddr = base
        self.CR = 0
        self.SR = 0x02 #TDRE=1
        self.TDR = 0
        self.RDR = 0
    
    def match(self,addr):
        if (addr>=self.baseAddr and addr<=self.baseAddr+1):
            return True
        return False

    def read(self,addr):
        if (addr == self.baseAddr):
            return self.SR
        if (addr == self.baseAddr+1):
            self.SR = self.SR & 0xFE
            return self.RDR
        
    def write(self,addr, val):
        if (addr == self.baseAddr):
            self.CR = val
        if (addr == self.baseAddr+1):
            self.SR = self.SR & 0xFD
            self.TDR = val

    #used to receive data from outside world
    def receive(self, data):
        self.RDR = data
        self.SR = self.SR | 0x01

    #used to transmit data to outside world
    def transmit(self):
        if self.SR & 0x02:
            return -1
        self.SR = self.SR | 0x02
        return self.TDR
