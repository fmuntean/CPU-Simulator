from MC6800.MC6800 import MC6800
from debugger import Debugger
from simulator import Simulator
from utils import loadHex

#from MC6802.acia import UART
from MC6800.st16c1550 import UART

ser = UART(0xFFF0) # Serial 

mem = bytearray(0xFFFF+1) # 64KB

def fetchMemory(address):
    if (ser.match(address)):
        return ser.read(address)
    else:
        return mem[address & 0xFFFF]

def setMemory(address, value):
    if (ser.match(address)):
        ser.write(address,value)
    else:
        #if address>0xE000:
        #    raise ValueError(f"Modifying ROM at 0x{address:4X}") 
        mem[address & 0xFFFF] = value

#loadHex(mem,"mc6802.hex")
#loadHex(mem,"swtb2.hex")
#loadHex(mem,"TB_6800.hex")

cpu = MC6800(fetchMemory,setMemory)

debugger = Debugger(cpu,mem)

simulator = Simulator()
simulator.Terminal = ser

if __name__ == '__main__':
   #loadHex(mem,"MC6800/mc6802.hex")
   loadHex(mem,"bios.hex")
   loadHex(mem,"TSCMicroBasicPlus/MicroBasROM.hex")
   cpu.reset()
   debugger.setROM(0xE000,0xFFEF)
   simulator.start(debugger)