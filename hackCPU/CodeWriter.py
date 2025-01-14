map_section={
  'constant':None,
  'local': 'LCL',
  'this': 'THIS',
  'that': 'THAT',
  'argument': 'ARG',
  'temp': 5,
  'pointer': 3
}

def cmd_push(arg1,arg2):
  ret = []

  if arg1=='static':
    ret = f"""
@{arg1}.{arg2}
D=M
@SP
A=M
M=D
@SP
M=M+1
"""
    return ret
  

  section = map_section[arg1]
  if section==None: # this is constant
    ret.append(f"@{arg2}\n")
    ret.append("D=A\n") # load the source value into D
  else:
    if section==5 or section==3: #this is the temp and pointer  
      ret.append(f"@{section+int(arg2)}\n")
      ret.append("D=M\n")
    else: 
      #TODO: Optimize for zero and 1 index
      ret.append(f"@{arg2}\n")
      ret.append("D=A\n")
      ret.append(f"@{section}\n")
      ret.append("A=D+M\n")
      ret.append("D=M\n")

  # D has the value to store
  ret.append("@SP\n") # get SP
  ret.append("A=M\n") # get the pointer 
  ret.append("M=D\n") # Add D to stack
  ret.append("@SP\n")
  ret.append("M=M+1\n") # increment SP
  return ret


"""
     pop segment i
addr ← segmentPointer + i
SP--
RAM[addr] ← RAM[SP]

@i
D=A ; push i into D
@Segment
D=D+A ; add segment + i into D

@R13
M=D ; store the segment+i into R13

@SP
M=M-1 ; decrement SP
D=M ; load value from SP into D

@R13
M=D ; load the value into the memory address stored in R13




"""
def cmd_pop(arg1,arg2):
  ret=[]
  

  if arg1=='static':
    ret = f"""
@SP
AM=M-1
D=M
@{arg1}.{arg2}
M=D
"""
    return ret
  
  section = map_section[arg1]
  # get the section pointer 
  # set pointer address to D
  if section==5 or section==3: #this is the temp  
    # get value from SP into D
    ret = f"""
    @SP
    AM=M-1
    D=M
    @{section+int(arg2)}
    M=D
    """
    
  else:
#TODO: Optimize for zero and 1 index

    ret.append(f"@{arg2}\n")
    ret.append("D=A\n")
    ret.append(f"@{section}\n")
    ret.append(f"D=D+M\n")
    # save the address to save value into R13
    ret.append("@R13\n")
    ret.append("M=D\n")
    
    #decrement SP and store the value into D
    ret.append("@SP\n")
    ret.append("AM=M-1\n")
    ret.append("D=M\n") 

    #store D into memory pointed by R13
    ret.append("@R13\n")
    ret.append("A=M\n")
    ret.append("M=D\n")
  return ret


def cmd_add():
  ret="""
@SP
AM=M-1
D=M
@SP
AM=M-1
A=M

D=D+A

@SP
A=M
M=D
@SP
M=M+1
  """
  return ret  


def cmd_sub():
  ret="""
@SP
AM=M-1
D=M
@SP
AM=M-1
A=M

D=A-D

@SP
A=M
M=D
@SP
M=M+1
  """
  return ret 

def cmd_and():
  ret="""
@SP
AM=M-1
D=M
@SP
AM=M-1
A=M

D=D&A

@SP
A=M
M=D
@SP
M=M+1
  """
  return ret 


def cmd_or():
  ret="""
@SP
AM=M-1
D=M
@SP
AM=M-1
A=M

D=D|A

@SP
A=M
M=D
@SP
M=M+1
  """
  return ret 


def cmd_eq(i):
  #True = -1 False = 0
  ret = f"""
@SP
AM=M-1
D=M
@SP
AM=M-1
A=M

D=A-D
@eq.skip.{i}
D;JEQ
D=0
@eq.end.{i}
0;JMP
(eq.skip.{i})
D=-1
(eq.end.{i})

@SP
A=M
M=D
@SP
M=M+1
"""
  return ret

def cmd_lt(i):
  #True = -1 False = 0
  ret = f"""
@SP
AM=M-1
D=M
@SP
AM=M-1
A=M

D=A-D
@lt.skip.{i}
D;JLT
D=0
@lt.end.{i}
0;JMP
(lt.skip.{i})
D=-1
(lt.end.{i})

@SP
A=M
M=D
@SP
M=M+1
"""
  return ret


def cmd_gt(i):
  #True = -1 False = 0
  ret = f"""
@SP
AM=M-1
D=M
@SP
AM=M-1
A=M

D=A-D
@gt.skip.{i}
D;JGT
D=0
@gt.end.{i}
0;JMP
(gt.skip.{i})
D=-1
(gt.end.{i})

@SP
A=M
M=D
@SP
M=M+1
"""
  return ret

def cmd_neg():
  ret="""
@SP
AM=M-1

M=-M

@SP
M=M+1
"""
  return ret

def cmd_not():
  ret="""
@SP
AM=M-1

M=!M

@SP
M=M+1
"""
  return ret

class CodeWriter:
  def __init__(self,asm):
    self.asm = asm
    self.counter=0

  def WriteComment(self,line):
    self.asm.writelines(line)
  
  def Translate(self,cmd,arg1,arg2):
    if cmd=='push':
      ret = cmd_push(arg1,arg2)
    elif cmd == 'pop':
      ret = cmd_pop(arg1,arg2)
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
      self.asm.writelines(ret)
      self.asm.writelines(["@123\n","@321\n"]) #for debugging only
    pass