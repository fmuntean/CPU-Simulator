
import curses

from threading import Thread
import time
from ScreenMemory import ScreenMemory
from sampleCPU.sampleCpu import myCPU
import debugger
import Simulator

mem = bytearray(256) # 256 bytes of memory


def fetchMemory(address):
    return mem[address & 0xFFFF]

def setMemory(address, value):
    mem[address & 0xFFFF] = value

cpu = myCPU(fetchMemory,setMemory)


debugger = debugger.Debugger(cpu,mem)

if __name__ == '__main__':
   Simulator.loadHex(mem,"sampleCPU/sample.hex")
   Simulator.start(debugger)
   