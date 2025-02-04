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
from  utils.vm_commands import *

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
  '':''
}



class CodeWriter:
  def __init__(self,asm):
    self.asm = asm
    self.counter=0
    self.source=''

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

  def WriteBoostrap(self):
    #lines = call_sys_init()
    #self.counter+=1
    #lines =call_sys_init() 
    #TODO: investigate as cmd_call might waste 5 bytes in stack instead of call_sys_init
    init_SP = """
      @256
      D=A
      @SP
      M=D
    """.splitlines()
    self.WriteLines(init_SP)
    lines= cmd_call("Sys.init",0,self.counter)
    self.WriteLines(lines)
    pass


  def Translate(self,cmd:string,arg1:string,arg2:int):
    
    if cmd=='label':
      ret = cmd_label(arg1)
    elif cmd=='goto':
      ret = cmd_goto(arg1)
    elif cmd=='if-goto':
      ret = cmd_if_goto(arg1)
    elif cmd=='call':
      self.counter+=1
      ret = cmd_call(arg1,arg2,self.counter)
    elif cmd=='function':
      ret = cmd_function(arg1,arg2)
    elif cmd=='return':
      ret = cmd_return()
    else:

      section = map_section[arg1]
      if cmd=='push':
        ret = cmd_push(section,arg2,self.source)
      elif cmd == 'pop':
        ret = cmd_pop(section,arg2,self.source)
      elif cmd == 'push-short':
        ret = cmd_push_short(section,arg2,self.source)
      elif cmd == 'pop-short':
        ret = cmd_pop_short(section,arg2,self.source)
        

      elif cmd == 'add':
        ret = cmd_add()
      elif cmd=='sub':
        ret = cmd_sub()
      
      elif cmd == 'eq':
        self.counter+=1
        ret = cmd_eq(self.counter)
      elif cmd == 'lt':
        self.counter+=1
        ret = cmd_lt(self.counter)
      elif cmd == 'gt':
        self.counter+=1
        ret = cmd_gt(self.counter)
      elif cmd == 'le':
        self.counter+=1
        ret = cmd_le(self.counter)
      elif cmd == 'ge':
        self.counter+=1
        ret = cmd_ge(self.counter)
      
      elif cmd=='and':
        ret = cmd_and()
      elif cmd=='or':
        ret = cmd_or()
      
      elif cmd=='neg':
        ret = cmd_neg()
      elif cmd=='not':
        ret = cmd_not()
      
      else:
        ret=None
    
    if ret != None:
      self.WriteLines(ret)
      #self.asm.writelines(["@123","@321"]) #for debugging only
    pass