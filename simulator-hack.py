'''
 Hack Computer simulator

'''


from debuggerSrv import Debugger
from hackCPU.hackCPU import hackCPU
from hackCPU.screen import Screen
from simulator import Simulator
from utils import loadMem

ram = [0x0000] * 32768  # 32K words of memory
rom = [0x0000] * 32768  # 32K words of ROM

def fetchInstruction(address):
    return rom[address &0x7FFF]

def fetchMemory(address):
    return ram[address & 0x7FFF]

def setMemory(address, value):
    ram[address & 0x7FFF] = value

cpu = hackCPU(fetchInstruction,fetchMemory,setMemory)

#define the simulator board
simulator = Simulator(cpu,ram,[])

#hookup the debugger to the simulator board
debugger = Debugger(simulator)

screen = Screen(fetchMemory,setMemory)  # Create a screen object
#Screen also implements keyboard


if __name__ == '__main__':
    # Start the screen in a separate thread
   screen.start()
   
   loadMem(rom,"hackCPU/pong.rom")
   #loadMem(rom,"hackCPU/Lab06/Rect.rom")
   #loadMem(rom,"hackCPU/hackCPU.rom")
   cpu.reset()
   
   simulator.isRunning = False #set this to true if you want to start or false to not run the code
   simulator.start()
   debugger.start()
   
   simulator.join() # wait here


   screen.stop()
   