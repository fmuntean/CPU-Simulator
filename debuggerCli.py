import socket
from threading import Thread
from utils import loadHex,loadS19

class Debugger():
    
    def __init__(self):
        self.displayStart = 0
        self.logging = False
        self.isRunning = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = ('127.0.0.1',54321)

    

    def log(self):
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
        cmd = b'list_cmd' if address is None else f"list_cmd,{address}".encode()
        self.socket.sendall(cmd)
        ret = self.socket.recv(1024).decode()
        return ret
    

    def get_opcodes(self,address=None):
        cmd = b'get_opcodes' if address is None else f"get_opcodes,{address}".encode()
        self.socket.sendall(cmd)
        ret = self.socket.recv(1024).decode()
        return ret

    def list_regs(self):
        self.socket.sendall(b'list_regs')
        ret = self.socket.recv(1024).decode()
        return ret
    
    def list_mem(self,start,length):
      self.socket.sendall(f"list_mem,{start},{length}".encode())
      ret = self.socket.recv(1024).decode()
      return ret.split("/r/n")

    def get_mem(self,start,length):
      self.socket.sendall(f"get_mem,{start},{length}".encode())
      ret = self.socket.recv(1024).decode()
      return ret.split("/r/n")

    def execute(self,cmd):
      cmd = cmd.replace(' ',',').lower()
        
      if cmd.startswith("display"):
        s = cmd.split(',')
        self.displayStart = int(s[1],base=16)        
        return "ok"
      
      if cmd.startswith("save"):
         s=cmd.split(',')
         if s[1].endswith('.bas'):
            cmd+=",D000,DFFF"
            
      if cmd.startswith("load"):
         s=cmd.split(',')
         if s[1].endswith('.bas'):
            cmd+=",D000"
      
      self.socket.sendall(cmd.encode())
      ret = self.socket.recv(1024).decode()
      return ret

        
         
            
    def start(self):
      self.socket.connect(self.addr)
