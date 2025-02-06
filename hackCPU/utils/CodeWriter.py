"""
  The hack computer VM considers the memory mapped the following way:

The first registers contains the pointers for the Stack and base addresses for the sections
  R0 = SP   ( 256)
  R1 = LCL  ( 300)
  R2 = ARG  ( 400)
  R3 = THIS (3000)
  R4 = THAT (3010)

R1 to R4 should not be modified as they used as base address only

# pointer section is the R3 and R4 only
# temp section is the R5 to R12

R13 to R15 are the only available Registers that can be used to store data

Static variables are kept in RAM between 16 and 255
Stack is between 256 and 2047

Heap starts at 2048

Screen Memory starts at 16384 and is 8K long
Keyboard is mapped immediately after at 24576

"""


import string

from utils import vm_commands1,vm_commands2,vm_commands3

map_section={
  'constant':None,
  'local': 'LCL',
  'this': 'THIS',
  'that': 'THAT',
  'argument': 'ARG',
  'temp': 5,
  'pointer': 3,
  'static':'static',
  None:None,
  '':'',
  'SP':'SP'
}



class CodeWriter:
  def __init__(self,asm):
    self.asm = asm # the asm file object where we write the opcodes
    self.counter=0 # a counter for the labels
    self.source='' #the name of the source vm file
    

  def WriteComment(self,line:string):
    self.asm.writelines(line)
    if line[-1] != '\n':
      self.asm.write('\n')
  
  def WriteLines(self,lines):
    for l in lines:
      line = l.lstrip().rstrip()
      if len(line)==0:
        continue
      self.asm.writelines(line+'\n')

  def WriteBootstrap(self):
    init_SP = self.commands.bootstrap()
    self.WriteLines(init_SP)
    lines= self.commands.cmd_call("Sys.init",0,self.counter)
    self.WriteLines(lines)
    pass



  def Translate(self,cmd:string,arg1:string,arg2:int):
    if cmd=='label':
      ret = self.commands.cmd_label(arg1)
    elif cmd=='goto':
      ret = self.commands.cmd_goto(arg1)
    elif cmd=='if-goto':
      ret = self.commands.cmd_if_goto(arg1)
    elif cmd=='call_global':
      ret = self.commands.cmd_call_global()
    elif cmd=='call':
      self.counter+=1
      ret = self.commands.cmd_call(arg1,arg2,self.counter)
    elif cmd=='function':
      ret = self.commands.cmd_function(arg1,arg2)
    elif cmd=='return_global':
      ret = self.commands.cmd_return_global()
    elif cmd=='return':
      ret = self.commands.cmd_return()
    
    elif cmd=='jmp':
      ret = self.commands.cmd_jmp(arg1)
    
    else:

      section = map_section[arg1]
      if cmd=='push':
        ret = self.commands.cmd_push(section,arg2,self.source)
      elif cmd == 'pop':
        ret = self.commands.cmd_pop(section,arg2,self.source)
      elif cmd == 'push-short':
        ret = self.commands.cmd_store_into_D(section,arg2,self.source)
      elif cmd == 'pop-short':
        ret = self.commands.cmd_pop_from_D(section,arg2,self.source)
        

      elif cmd == 'add':
        ret = self.commands.cmd_add()
      elif cmd=='sub':
        ret = self.commands.cmd_sub()
      
      elif cmd == 'eq':
        self.counter+=1
        ret = self.commands.cmd_eq(self.counter)
      elif cmd == 'lt':
        self.counter+=1
        ret = self.commands.cmd_lt(self.counter)
      elif cmd == 'gt':
        self.counter+=1
        ret = self.commands.cmd_gt(self.counter)
      elif cmd == 'le':
        self.counter+=1
        ret = self.commands.cmd_le(self.counter)
      elif cmd == 'ge':
        self.counter+=1
        ret = self.commands.cmd_ge(self.counter)
      
      elif cmd=='and':
        ret = self.commands.cmd_and()
      elif cmd=='or':
        ret = self.commands.cmd_or()
      
      elif cmd=='neg':
        ret = self.commands.cmd_neg()
      elif cmd=='not':
        ret = self.commands.cmd_not()

      elif cmd=='inc':
        ret = self.commands.cmd_inc(section,arg2)
      elif cmd=='dec':
        ret = self.commands.cmd_dec(section,arg2)
      else:
        ret=None
    
    if ret != None:
      self.WriteLines(ret)
      
    pass