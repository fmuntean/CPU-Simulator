from threading import Thread


def cmd_run(dbg):
    step = True
    while step:
        if (dbg.breakpoint == dbg.cpu.PC):
            return
        if dbg.logging:
            dbg.log(dbg.list_cmd(dbg.cpu.PC))    
        try:
            step = dbg.cpu.step()
        except ROMError as err:
            return err

class ROMError(Exception): ...

class Debugger:
    protect = [] # an array of tuples of memory ranges to protect from writing
    def __init__(self,cpu,mem):
        self.cpu = cpu
        self.mem = mem
        self.displayStart = 0
        self.breakpoint = -1 #means disabled
        self.logging = False

    def setMemoryProtected(address, value):
        for start,end in Debugger.protect:
            if address>=start and address<=end:
                raise ROMError(f"ROM protected Area: 0x{address:4X}")
        Debugger.setMemory(address,value)
        
    def setROM(self,fromAddr,toAddr):
        #we add a protect range
        Debugger.protect.append([fromAddr,toAddr])
        #we hijack the cpu setMemory method
        Debugger.setMemory = self.cpu.setMemory
        self.cpu.setMemory = Debugger.setMemoryProtected

    def log(self,line):
        if self.logging:
            file1 = open("debugger.log", "a")  # append mode
            file1.write(self.list_regs(self.cpu))
            file1.write('| |')
            opcodes = self.get_opcodes(self.cpu.PC)
            file1.write(opcodes)
            match len(opcodes):
                case 2:
                    file1.write('      ')
                case 5:
                    file1.write('   ')
            file1.write('| ')
            file1.write(self.list_cmd(self.cpu.PC))
            file1.write("\n")
            file1.close()
        return

    def list_cmd(self,address=None):
        address = self.cpu.PC if address == None else address
        o = self.cpu.getOpcode(address)
        if o == None:
            return "unknown"
        ret = o.decode(self.cpu, address)
        return ret
    
    def get_opcodes(self,address=None):
        address = self.cpu.PC if address==None else address
        o = self.cpu.getOpcode(address)
        if o == None:
            return f"{self.mem[address & 0xFFFF]:02X}"
        ret=self.mem[address:address+o.length]
        return ret.hex(' ').upper()

    def list_regs(self):
        return self.cpu.getRegisters()
    
    def list_mem(self,start,length):
        i = start
        ret = []
        for x in range(0, length // 8):
            s=f"{(i+8*x)&0xFFFF:04X}:"
            for y in range(0,8):
                s+=f" {self.mem[(i+8*x+y) & 0xFFFF]:02X}"
            ret.append(s)
        return ret


    def execute(self,cmd):
        cmd = cmd.lower()
        if cmd == "reset":
            self.cpu.reset()
            return "ok"

        if cmd == "step":
            self.log(self.list_cmd(self.cpu.PC))
            self.cpu.step()
            ret = self.list_cmd(self.cpu.PC)
            return ret
        
        if cmd.startswith('break'):
            cmd = cmd.replace(' ',',')
            s = cmd.split(',')
            
            #by default we use base 16 and we prefix with d for decimal values
            if s[1].startswith('d'): 
                v = int(s[1],base=10)
            else:
                v= int(s[1],base=16)

            self.breakpoint = v
            return "ok"
            
        if cmd.startswith("jump"):
            s = cmd.split(',')
            if len(s)>1:
                if s[1].startswith('0x'):
                    a = int(s[1],base=16)
                else:
                    a= int(s[1],base=10)
                self.cpu.PC=a

        if cmd.startswith("run"):
            s = cmd.split(',')
            if len(s)>1:
                if s[1].startswith('0x'):
                    a = int(s[1],base=16)
                else:
                    a= int(s[1],base=10)
                self.cpu.PC=a
            thread = Thread(target=cmd_run, args=(self,))
            thread.start()
            return thread

        if cmd.startswith("set"):
            s = cmd.split(',')
            a = int(s[1])
            v = int(s[2])
            self.mem[a] = v
            return f"{a} : {v}"
             
        if cmd.startswith("get"):
            s = cmd.split(',')
            a = int(s[1])
            v =self.mem[a]
            return f"{a} : {v}"
        
        if cmd.startswith("save"):
            s = cmd.split(',')
            f = s[1]
            file = open(f, "w+b")
            binary_format = bytearray(self.mem)
            file.write(binary_format)
            file.close()
            return "saved"
        
        if cmd.startswith("load"):
            s = cmd.split(',')
            f = s[1]
            if (f.endswith("mem")):
                file = open(f, "rb")
                
                bytes = file.read(256)
                file.close()
                for i in range(0,255):
                    self.mem[i] = bytes[i]
            elif (f.endswith("hex")):
                loadHex(self.mem,f)
            else:
                loadS19(self.mem,f)
            
            return "loaded"
        
        if cmd.startswith("display"):
            s = cmd.split(',')
            self.displayStart = int(s[1],base=16)        
            return "ok"
        
        if cmd.startswith("int"): #simulates an interrupt
            o = self.cpu.getOpcode(self.cpu.PC)
            if o == None:
                return "Invalid opcode"
            if o.text == "WAI":
                o.execute(self.cpu, stage=1)
                return "ok"
            return "CPU not on WAI opcode"

        if cmd.startswith("log"): 
            s = cmd.split(',')
            if s[1]=='1' or s[1]=='on':
                self.logging = True
            else:
                self.logging = False
            return "ok"
        return "Invalid Command!" 
            
