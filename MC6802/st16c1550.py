# ST16C1550 (Asynchronous Communication) simulator

class UART:
    def __init__(self, base):
        self.baseAddr = base
        #registers reset condition
        self.RHR = 0        #Receive Holding Register   (read only)
        self.THR = 0        #Transmit Holding Register  (write only)
        self.IER = 0x00     #Interrupt Enable Register
        self.ISR = 0x01     #Interrupt Status Register  (Read Only)
        self.FCR = 0x00     #FIFO Control Register      (write only)
        self.LCR = 0x00     #Line Control Register
        self.MCR = 0x00     #Modem Control Register
        self.LSR = 0x60     #Line Status Register       (read only)
        #bits 0-3 are 0 but the bits 4-7 are inputs reversed (DSR,CTS,CD,RI)
        self.MSR = 0        #Modem Status Register      (read only)
        self.SPR = 0xFF     #Scratch Pad Register
        self.DLL = 0        #Baud rate  Generator Divider Low     
        self.DLM = 0        #Baud rate  Generator Divider High
        #DTR and RTS outputs are set to logic 1 on reset
        
    def match(self,addr):
        if (addr>=self.baseAddr and addr<=self.baseAddr+8):
            return True
        return False

    #read internal register 
    def read(self,addr):
        a02 = addr - self.baseAddr
        if a02 == 0:
            if self.LCR & 0x80 == 0:
                self.LSR = self.LSR & 0xFE # we mark the register as empty
                return self.RHR
            else:
                return self.DLL
        if a02 == 1:
            if self.LCR & 0x80 == 0:
                return self.IER
            else:
                return self.DLM
        if a02 == 2:
            return self.ISR
        if a02 == 3:
            return self.LCR
        if a02 == 4:
            return self.MCR
        if a02 == 5:
            return self.LSR
        if a02 == 6:
            return self.MSR
        if a02 == 7:
            return self.SPR
        
    #write internal registers
    def write(self,addr, val):
        a02 = addr - self.baseAddr
        if a02 == 0:
            if self.LCR & 0x80 == 0:
                self.THR = val
                self.LSR = self.LSR & 0xDF # we reset the empty flag
            else:
                self.DLM = val
        if a02 == 1:
            self.IER = val
        if a02 == 2:
            self.FCR = val
        if a02 == 3:
            self.LCR = val
        if a02 == 4:
            self.MCR = val
        if a02 == 7:
            self.SPR = val

    #used to receive data from outside world
    def receive(self, data):
        self.RHR = data
        self.LSR = self.LSR | 0x01  # we flag that the RHR has data

    #used to transmit data to outside world
    def transmit(self):
        if self.LSR & 0x20: # the flag is 1 when empty
            return -1
        self.LSR = self.LSR | 0x20 # we flag that the THR is empty
        return self.THR
