import socket
from threading import Thread
from utils import loadHex,loadS19


class Debugger(Thread):
    
    def __init__(self,simulator):
        Thread.__init__(self,name="DebuggerThread")
        self.cpu = simulator.cpu
        self.mem = simulator.mem
        self.displayStart = 0
        self.breakpoint = -1 #means disabled
        self.logging = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.isRunning=False
        self.port = 54321
        self.ip = '127.0.0.1'

 
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
        if cmd == 'list_regs':
            return self.list_regs()
        
        if cmd.startswith('list_cmd'):
            cmd = cmd.replace(' ',',')
            s = cmd.split(',')
            if len(s)==1:
                return self.list_cmd()
            
            #by default we use base 16 and we prefix with d for decimal values
            if s[1].startswith('d'): 
                addr = int(s[1],base=10)
            else:
                addr= int(s[1],base=16)
            
           
            return self.list_cmd(addr)
        
        
        if cmd.startswith('get_opcodes'):
            cmd = cmd.replace(' ',',')
            s = cmd.split(',')
            if len(s)==1:
                return self.get_opcodes()
            
            #by default we use base 16 and we prefix with d for decimal values
            if s[1].startswith('d'): 
                addr = int(s[1],base=10)
            else:
                addr= int(s[1],base=16)
            
           
            return self.get_opcodes(addr)
        
        if cmd.startswith('list_mem'):
            cmd = cmd.replace(' ',',')
            s = cmd.split(',')
            #by default we use base 16 and we prefix with d for decimal values
           
            start = int(s[1],base=10)
            
            #by default we use base 16 and we prefix with d for decimal values
            length = int(s[2],base=10)
            
            ret = self.list_mem(start,length)

            return '/r/n'.join(ret)


        if cmd == "reset":
            self.cpu.reset()
            return "ok"

        if cmd == "step":
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
            



    def run(self):
        self.isRunning=True
        self.socket.bind((self.ip,self.port))
        print(f"debugger server listening on {self.ip} port {self.port}")
        while self.isRunning:
            try:
                self.socket.listen(1)
                c,addr = self.socket.accept()
                #c.send("Debugger connected\r\n".encode())
                while self.isRunning:
                    try:  
                        msg = c.recv(1024).decode()
                        print(f"DBG: got message: {msg}")
                        ret = self.execute(msg)
                        print(f"DBG: response: {ret}")
                        c.sendall(ret.encode())
                    except socket.timeout:
                        print("socket timeout")
                        continue
                    
                c.close()
            except Exception as e:
                print(f"socket exception: {type(e)}")
                print(e)
                continue
        