

from sampleCPU.sampleCpu import myCPU
from debuggerSrv import Debugger
from Simulator import Simulator
from utils import loadHex

mem = bytearray(256) # 256 bytes of memory


def fetchMemory(address):
    return mem[address & 0xFFFF]

def setMemory(address, value):
    mem[address & 0xFFFF] = value

cpu = myCPU(fetchMemory,setMemory)

#define the simulator board
simulator = Simulator(cpu,mem,None)

#hookup the debugger to the simulator board
debugger = Debugger(simulator)


if __name__ == '__main__':
   
   loadHex(mem,"cpu-simulator/sampleCPU/sample.hex")
   cpu.reset()
   
   simulator.isRunning = False
   simulator.start()
   debugger.start()
   
   simulator.join() # wait here