from MC6800.MC6800 import MC6800
from debugger import Debugger
import Simulator

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
        mem[address & 0xFFFF] = value

#debugger.loadHex(mem,"mc6802.hex")
#debugger.loadHex(mem,"swtb2.hex")
#debugger.loadHex(mem,"TB_6800.hex")

cpu = MC6800(fetchMemory,setMemory)

debugger = Debugger(cpu,mem)

if __name__ == '__main__':
   Simulator.loadHex(mem,"MC6800/mc6802.hex")
   Simulator.start(debugger)