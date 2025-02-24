from threading import Thread
from time import sleep


class ROMError(Exception): ...


class Simulator(Thread):
  def __init__(self,cpu,mem,devices) -> None:
    Thread.__init__(self,name="SimulatorThread")
    self.cpu = cpu
    if devices is not None:
      cpu.fetchMemory = self.fetchMemory
      cpu.setMemory = self.setMemory
    self.mem = mem
    self.devices = devices
    self.protect = [] # an array of tuples of memory ranges to protect from writing
    self.isRunning = False
    self.delay=0
    self.breakpoint = -1
    pass

  def fetchMemory(self,address,peek=False):
    for d in self.devices:
      if (d.match(address)):
          return d.read(address,peek)
      else:
          return self.mem[address % len(self.mem)]

    return self.mem[address % len(self.mem)]

  def setMemory(self, address, value):
    if len(self.devices)==0:
       self.mem[address % len(self.mem)] = value
    for d in self.devices:
      if (d.match(address)):
          d.write(address,value)
      else:
        for start,end in self.protect:
            if address>=start and address<=end:
                raise ROMError(f"ROM protected Area: 0x{address:4X}")
        self.mem[address & 0xFFFF] = value
    
        
  def setROM(self,fromAddr,toAddr):
    #we add a protect range
    self.protect.append([fromAddr,toAddr])

  def run(self):
    print("Simulator running")
    while True:
      if self.isRunning:    
        try:
          step = self.cpu.step()
          if (self.breakpoint == self.cpu.PC):
            self.isRunning = False
          if self.delay>0:
             sleep(self.delay)
        except ROMError as err:
            self.isRunning = False
    pass
  

  def pause(self):
     self.isRunning = False

  
