import string

def cmd_push(section:string,arg2:int):
  
  if section=='static':
    ret = f"""
      @{section}.{arg2}
      D=M   //read from static memory to D
      @SP   //add D into Stack
      A=M
      M=D
      @SP   //increment stack pointer
      M=M+1
    """
    return ret.splitlines()
  
  ret = []
  if section==None: # this is a constant number stored into arg2
    if arg2<-1 or arg2>1:
      ret.append(f"@{arg2}")
      ret.append("D=A  //load the source value into D")

    ret.append("@SP  //select stack") # get SP
    ret.append("A=M") # get the pointer 
    if arg2 in (-1,0,1):
      ret.append(f"M={arg2}")
    else:
      ret.append("M=D") # Add D to stack
    
    ret.append("@SP  //increment stack pointer")
    ret.append("M=M+1") # increment SP
    return ret
  else:
    if section==5 or section==3: #this is the temp and pointer
      if section==3 and arg2>1:
        ret.append("#ERR: invalid index for pointer section only [0;1] allowed")  
      if section==5 and arg2>7:
        ret.append("#ERR: invalid index for temp section only [0;7] allowed")
      
      ret.append(f"@{section+arg2}")
      ret.append("D=M")
    else: 
      if arg2>1:
        ret.append(f"@{arg2}")
        ret.append("D=A")
      ret.append(f"@{section}")
      if arg2>1:
        ret.append("A=D+M")
      if arg2==1:
        ret.append("A=M+1")
      ret.append("D=M")

  # D has the value to store
  ret.append("@SP") # get SP
  ret.append("A=M") # get the pointer 
  ret.append("M=D") # Add D to stack
  ret.append("@SP")
  ret.append("M=M+1") # increment SP
  return ret


"""
     pop segment i
addr ← segmentPointer + i
SP--
RAM[addr] ← RAM[SP]
"""
def cmd_pop(section:string,arg2:int):
  ret=[]
  

  if section=='static':
    ret = f"""
      @SP
      AM=M-1
      D=M
      @{section}.{arg2}
      M=D
    """
    return ret.splitlines()
  
  # get the section pointer 
  # set pointer address to D
  if section==5 or section==3: #this is the temp  
    # get value from SP into D
    ret = f"""
    @SP
    AM=M-1
    D=M
    @{section+arg2}
    M=D
    """
    return ret.splitlines()
    
  else:
    #Optimize for zero and 1 index
    if arg2==0:
      ret=f"""
        @SP
        AM=M-1
        D=M
        @{section}
        M=D
      """
      return ret.splitlines()

    if arg2>1:
      ret.append(f"@{arg2}")
      ret.append("D=A")
    ret.append(f"@{section}")
    if arg2==1:
      ret.append("A=M+1")
    if arg2>1:  
      ret.append("A=D+M")
    ret.append("D=M")
    # save the address to save value into R13
    ret.append("@R13")
    ret.append("M=D")
    
    #decrement SP and store the value into D
    ret.append("@SP")
    ret.append("AM=M-1")
    ret.append("D=M") 

    #store D into memory pointed by R13
    ret.append("@R13")
    ret.append("A=M")
    ret.append("M=D")
  return ret


def cmd_add():
  ret="""
    @SP
    AM=M-1
    D=M
    @SP
    AM=M-1
    
    M=D+M

    @SP
    M=M+1
  """
  return ret.splitlines()


def cmd_sub():
  ret="""
    @SP
    AM=M-1
    D=M
    @SP
    AM=M-1

    M=M-D

    @SP
    M=M+1
  """
  return ret.splitlines() 

def cmd_and():
  ret="""
    @SP
    AM=M-1
    D=M
    @SP
    AM=M-1
    
    M=D&M

    @SP
    M=M+1
  """
  return ret.splitlines() 


def cmd_or():
  ret="""
    @SP
    AM=M-1
    D=M
    @SP
    AM=M-1
    
    M=D|M

    @SP
    M=M+1
  """
  return ret.splitlines() 


def cmd_eq(i:int):
  #True = -1 False = 0
  ret = f"""
    @SP
    AM=M-1
    D=M
    @SP
    AM=M-1
    
    D=D-M
    @eq.true.{i}
    D;JEQ
    D=-1
    (eq.true.{i})
    D=!D

    @SP
    A=M
    M=D
    @SP
    M=M+1
  """
  return ret.splitlines()

def cmd_lt(i:int):
  #True = -1 False = 0
  ret = f"""
    @SP
    AM=M-1
    D=M
    @SP
    AM=M-1

    D=M-D
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
  return ret.splitlines()


def cmd_gt(i:int):
  #True = -1 False = 0
  ret = f"""
    @SP
    AM=M-1
    D=M
    @SP
    AM=M-1

    D=M-D
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
  return ret.splitlines()

def cmd_neg():
  ret="""
    @SP
    AM=M-1

    M=-M

    @SP
    M=M+1
  """
  return ret.splitlines()

def cmd_not():
  ret="""
    @SP
    AM=M-1

    M=!M

    @SP
    M=M+1
  """
  return ret.splitlines()