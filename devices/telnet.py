# object to handle the telnet protocol

import socket
import threading
#from multiprocessing import Process


class Telnet(threading.Thread):

  def __init__(self,onSend,onReceive):
    threading.Thread.__init__(self,name="TelnetThread")
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    self.onSend = onSend
    self.onReceive = onReceive
    self.isRunning=True
    self.port = 12345
    self.ip = '127.0.0.1'
    

  def run(self):
    self.socket.bind((self.ip,self.port))
    print(f"telnet server listening on {self.ip} port {self.port}")
    
    self.socket.listen(1)
    c,addr = self.socket.accept()
    c.settimeout(0.1)
    c.send("Simulator connected\r\n".encode())
    while self.isRunning:
      chr = self.onSend()
      if chr is not None:
        c.sendall(bytes([chr]))
      try:  
        chr = c.recv(1)[0]
        if chr is not None:
          self.onReceive(chr)
      except socket.timeout:
        continue

    c.close()

    
    



