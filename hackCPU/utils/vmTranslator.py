from utils import Parser, vm_commands1,vm_commands2,vm_commands3
from utils.CodeWriter import CodeWriter


class VMTranslator:
  def __init__(self,parser:Parser,writer:CodeWriter,version=1):
    self.parser = parser
    self.writer = writer
    self.Translate = self.Translate1

    if version==1:
      writer.commands = vm_commands1
      
      writer.WriteBootstrap()

    if version==2:
      writer.commands = vm_commands2
      writer.WriteBootstrap()

    if version==3:
      writer.commands = vm_commands2
      
      writer.WriteBootstrap()
      # vm_return command is big and does not require any parameters as it only uses the stack as the input
      # we can generate the code for it once and we keep calling it directly
      self.writer.Translate('return_global',None,0)

    if version==4:
      writer.commands = vm_commands3
    
      writer.WriteBootstrap()
      # vm_return command is big and does not require any parameters as it only uses the stack as the input
      # we can generate the code for it once and we keep calling it directly
      self.writer.Translate('return_global',None,0)

      
      self.writer.Translate('call_global',None,0)
  
    pass



  
  def Translate1(self,f):
        for line in f:
          if len(line)==0:
            continue
          if line =='\n':
            continue
          if line.strip().startswith('//'):
            self.writer.WriteComment(line)
            continue
          
          self.writer.WriteComment(f"\n//{line}")
          
          cmd,arg1,arg2 = self.parser.Parse(line)
          arg2 = 0 if arg2 in (None,'','//')  else int(arg2)
          self.writer.Translate(cmd,arg1,arg2)


  """
Build a state machine that calls micro instructions 
 Call function:
  D = return address
  R13 = nArgs numbers of arguments or internal vars
  R14 = function to call
  R15 = unused

 Return function:
  D   =
  R13 = return address 
  R14 =
  R15 = unused


  only implemented the: 
    call + return
    lt,eq,gt

  
  
    @ first instruction
    D=A   //load first instruction address
    @R14
    M = D //store this address into R14
  
  (sm_loop)
    @R14
    A=M //load address from R14
    0;JMP  //jump to this address

  (first_instruction)
    push constant 0
    
    @{second_instr}
    D=A   //load next instruction
    @R14
    M=D   //load next instruction in R14
    @sm_loop
    0;JMP




  """
  def Translate2(self,f):
    for line in f:
      if len(line)==0:
        continue
      if line =='\n':
        continue
      if line.strip().startswith('//'):
        self.writer.WriteComment(line)
        continue
      
      self.writer.WriteComment(f"\n//{line}")
      
      cmd,arg1,arg2 = self.parser.Parse(line)
      arg2 = 0 if arg2 in (None,'','//')  else int(arg2)
      self.writer.Translate(cmd,arg1,arg2)
    pass     