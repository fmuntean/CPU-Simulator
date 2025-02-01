"""
VMOptimizer
- loads the vm Files one by one 
- and finds patterns of commands that can be optimized to reduce the size

"""



import os
import re
import string
from sys import argv

from sympy import true



class Parser:
  input = []

  def Parse(f):
    Parser.input+=f.readlines()
    
  def add(line):
    Parser.input.append(line)


class VMOptimizer:
  def __init__(self):
    self.counts={}
    pass

  def save(self,f):
    f.writelines(Parser.input)

  def count(self,type):
    if type in self.counts.keys():
      self.counts[type]+=1
    else:
      self.counts[type]=1

  def printCounts(self):
    print("\nOptimization Counts:\n")
    for k,v in self.counts.items():
      print(f"{k}={v:04d}\n")

  def Optimize(self):
    i = 0
    while i<len(Parser.input)-1:
      if self.is_doubleNot(i):
        Parser.input.pop(i)
        Parser.input.pop(i)
        self.count('doubleNot')

      if self.is_inc(i):
        Parser.input.pop(i)
        Parser.input[i]="\tinc //increment\n"
        self.count('inc')

      if self.is_dec(i):
        Parser.input.pop(i)
        Parser.input[i]="\tinc //increment\n"
        self.count('dec')

      if self.is_shortPushPop(i): # we only need to push/pop data into D register
        Parser.input[i].replace('push','push-short')
        Parser.input[i+1].replace('pop','pop-short')
        self.count('shortPushPop')

      #if self.is_unnecessaryPop(i):
      #  print()
      
      i+=1
    pass


  def is_doubleNot(self,i):
    l1 = Parser.input[i]
    l2 = Parser.input[i+1]
    if 'not' in l1 and l1==l2:
      return True
    return False
      
  def is_unnecessaryPop(self,i):
    #call Ball.show 1
    #pop temp 0
    #push this 14
    if i==0:
      return False
    
    l1 = Parser.input[i-1]
    l2 = Parser.input[i]
    l3 = Parser.input[i+1]
    if 'call' in l1 and 'pop temp 0' in l2 and 'push' in l3:
      print(f"\n{l1}\t{l2}\t{l3}\n")
      return True
    return False
  

  def is_shortPushPop(self,i):
    l1 = Parser.input[i]
    l2 = Parser.input[i+1]
    if 'push' in l1 and 'pop' in l2:
      print(f"\n{l1}\t{l2}\n")
      return True
    return False
  

  #push constant 1
  #add
  def is_inc(self,i):
    l1 = Parser.input[i]
    l2 = Parser.input[i+1]
    if 'push constant 1' in l1 and 'add' in l2:
      print(f"\n{l1}\t{l2}\n")
      return True
    return False
  
  #push constant 1
  #sub
  def is_dec(self,i):
    l1 = Parser.input[i]
    l2 = Parser.input[i+1]
    if 'push constant 1' in l1 and 'sub' in l2:
      print(f"\n{l1}\t{l2}\n")
      return True
    return False
  

def getVMFiles(folder:string):
  ret =[]
   # r=root, d=directories, f = files
  for r, d, f in os.walk(vmFolder):
    for file in f:
      if file.endswith(".vm"):
          ret.append(os.path.join(r, file))
  return ret



if __name__ == '__main__':
  vmFolder = 'lab11\\Pong'


  outFile = vmFolder.split(os.path.sep)[-1]+"-optimized.vm"  
  with open(outFile,mode="w") as asm:
    for vmFile in getVMFiles(vmFolder):
      with open(vmFile,mode="r") as f:
        _,sourceFile=os.path.split(vmFile)
        Parser.add(f"\n// Processing file: {vmFile}\n")
        Parser.Parse(f)
    
    translator = VMOptimizer()
    translator.Optimize()
    translator.printCounts()
    translator.save(asm)

    