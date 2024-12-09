from MC6800.MC6800 import MC6800
from debuggerSrv import Debugger
from simulator import Simulator
from utils import loadHex

#from devices.acia import UART
#from devices.st16c1550 import UART
from devices.z8530 import UART

from devices.telnet import Telnet


ser = UART(0xc7f4) # Serial device at specific address

#redirect serial in/out over telnet protocol
telnet = Telnet(ser.transmit,ser.receive)


#allocate the memory
mem = bytearray(0xFFFF+1) # 64KB


# initialize the CPU
cpu = MC6800()

#define the simulator board
simulator = Simulator(cpu,mem,[ser])

#hookup the debugger to the simulator board
debugger = Debugger(simulator)

if __name__ == '__main__':
   print("\r\n")
   #loadHex(mem,"MC6800/mc6802.hex")
   loadHex(mem,"bios.hex")
   loadHex(mem,"TSCMicroBasicPlus/MicroBasROM.hex")
   #loadHex(mem,"TSCMicroBasicPlus/MicroBas.hex")
   
   cpu.reset()
   simulator.setROM(0x8000,0x8FFF)

   telnet.start()
   simulator.isRunning = True
   simulator.start()
   debugger.start()
   
   simulator.join() # wait here

    
   