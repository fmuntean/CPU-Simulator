

from sampleCPU.sampleCpu import myCPU
from debugger import Debugger
from simulator import Simulator

mem = bytearray(256) # 256 bytes of memory


def fetchMemory(address):
    return mem[address & 0xFFFF]

def setMemory(address, value):
    mem[address & 0xFFFF] = value

cpu = myCPU(fetchMemory,setMemory)


debugger = Debugger(cpu,mem)

if __name__ == '__main__':
   sim = Simulator()
   #Simulator.loadHex(mem,"sampleCPU/sample.hex")
   sim.start(debugger)
   