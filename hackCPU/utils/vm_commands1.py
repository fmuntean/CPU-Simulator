
"""

Implementation of the VM commands specific to the Hack CPU opcodes.

"""




import string


##########################################################################################
#    Standard hack commands
##########################################################################################

def cmd_push(section:string,arg2:int,source:string):
  
  if section=='static':
    ret = f"""
      @static.{source}.{arg2}
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
      if arg2==0:
        ret.append("A=M")
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
def cmd_pop(section:string,arg2:int,source:string):
  ret=[]
  

  if section=='static':
    ret = f"""
      @SP
      AM=M-1
      D=M
      @static.{source}.{arg2}
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
        A=M
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
    
    ret.append("D=A")
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
    @lt.end.{i}
    D=0;JMP
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
    @gt.end.{i}
    D=0;JMP
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


def cmd_label(lbl:string):
  return ([f"({lbl})"])

def cmd_goto(lbl:string):
  ret=f"""
    @{lbl}
    0;JMP
  """
  return ret.splitlines()

def cmd_if_goto(lbl:string):
  ret = f"""
    @SP
    AM=M-1
    D=M
    @{lbl}
    D;JNE   //not equal to zero
  """
  return ret.splitlines()


"""
push returnAddress  //use a label declared below
push LCL            //saves LCL into stack
push ARG            //saves ARG
push THIS           //saves THIS
push THAT           //saves THAT
ARG = SP-5-nArgs    //reposition ARG
LCL = SP            //reposition LCL
goto functionName   //jump to function label
(returnAddress)
"""
def cmd_call(fName:string,nArgs:int,i:int):
  ret=f"""
    @return_from_{fName}_{i}
    D=A
    @SP   //push returnAddress
    A=M
    M=D
    
    @LCL  //push LCL
    D=M
    @SP
    AM=M+1
    M=D
    
    @ARG  //push ARG
    D=M
    @SP
    AM=M+1
    M=D

    @THIS //push THIS
    D=M
    @SP
    AM=M+1
    M=D

    @THAT //push THAT
    D=M
    @SP
    AM=M+1
    M=D

    @SP
    MD=M+1

    @LCL  //LCL = SP (reposition LCL)
    M=D

    @{5+nArgs} //ARG = SP-5-nArgs   (reposition ARG)
    D=A
    @SP
    A=M
    D=A-D
    @ARG
    M=D
        
    @{fName}
    0;JMP    //jump to function label

    (return_from_{fName}_{i})
  """
  return ret.splitlines()


"""
(functionName)    //declare function label
repeat nVars times: push 0
"""
def cmd_function(label:string,nVars:int):
  ret = [f"({label})"]
  if nVars>0:
    ret.append("@SP")
    ret.append("A=M")
    for i in range(nVars):
      ret.append("M=0")
      ret.append("AD=A+1")
    ret.append("@SP")
    ret.append("M=D")
  return ret

"""
endFrame = LCL          // put LCL in a temp variable
retAddr= *(endFrame-5)  //gets the return address
*ARG = pop()            //reposition the return value (pop and copy to ARG)
SP=ARG+1                //reposition SP
THAT = *(endFrame-1)
THIS = *(endFrame-2)
ARG  = *(endFrame-3)
LCL  = *(endFrame-4)
goto retAddr
"""
def cmd_return():
  ret = """
    @LCL  
    D=M
    @R13  //save endFrame-1
    M=D-1
    @5
    A=D-A //calculate LCL-5
    D=M
    @R14  //save return address
    M=D

    @SP
    A=M-1
    D=M   //pop()
    @ARG
    A=M
    M=D   //set return value
    D=A+1 //reposition SP after return value
    @SP
    M=D

    @R13  //restore THAT
    A=M
    D=M
    @THAT
    M=D

    @R13 //restore THIS
    AM=M-1
    D=M
    @THIS
    M=D

    @R13 //restore ARG
    AM=M-1
    D=M
    @ARG
    M=D

    @R13  //restore LCL
    AM=M-1
    D=M
    @LCL
    M=D

    @R14
    A=M
    0;JMP

  """
  return ret.splitlines()

def call_sys_init():
  ret = """
    @Sys.init
    0;JMP
  """
  return ret.splitlines()

def bootstrap():
  ret= """
    @256
    D=A
    @SP
    M=D
  """
  return ret.splitlines()

def error(list,msg):
  list.append(msg)
  raise Exception(msg)