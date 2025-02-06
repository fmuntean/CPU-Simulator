
"""

Implementation of the VM commands specific to the Hack CPU opcodes.

"""




import string


##########################################################################################
#    Extra hack commands
##########################################################################################
#
# the current implementation did not use some of the existing opcodes or optimizations 
# adding few VM commands to help optimize the code or use opcodes like ge and le 
#
#
#
##########################################################################################

'''
Hack CPU does not have a stack register. Transferring to/from stack involves loads of instructions and memory access
Many times there is a need to just transfer one value from one place to another.

cmd_store_into_D
cmd_pop_from_D
  allow to transfer faster between registers or variables by pushing to D only instead all the way to the stack
  these needs to be used next to each other when reassigning values around. like let a=0 or let a=b

cmd_inc
cmd_dec
  many times there is a need to add 1 or subtract 1 from a variable.
  hackCPU has multiple opcodes to deal with this directly like M=M-1 or D=M-1
  these use optimized opcodes vs pushing 1 and variable to the stack then add them and then move it back to the memory

cmd_ge
cd_le
  these opcodes are not utilized in the original VM implementation
  if statements needed to use complex expression to go around like a<=b resulted in (a<b)|(a=b)
  using the opcodes directly simplify the expression and optimizes the code.
  


'''


def cmd_inc(section:string,arg2:int,source:string):
  if arg2==0:
    ret = f"""
      @{section}
      M=M+1
    """
    return ret.splitlines()
  if arg2==1:
    ret = f"""
      @{section}
      A=M+1
      M=M+1
    """
    return ret.splitlines()
  ret = f"""
    @{arg2}
    D=A
    @{section}
    A=D+M
    M=M+1
  """
  return ret.splitlines()

def cmd_dec(section:string,arg2:int,source:string):
  if arg2==0:
    ret = f"""
      @{section}
      M=M-1
    """
    return ret.splitlines()
  if arg2==1:
    ret = f"""
      @{section}
      A=M+1
      M=M-1
    """
    return ret.splitlines()
  ret = f"""
    @{arg2}
    D=A
    @{section}
    A=D+M
    M=M-1
  """
  return ret.splitlines()


"""
  we take the value from D register and we store where needed
"""
def cmd_pop_from_D(section:string,arg2:int,source:string):
  
  if section=='static':
    ret = f"""
      @static.{source}.{arg2}
      M=D
    """
    return ret.splitlines()
  
  if section==5 or section==3: #this is the temp  
    ret = f"""
    @{section+arg2}
    M=D
    """
    return ret.splitlines()
    
  
  #Optimize for zero index
  if arg2==0:
    ret=f"""
      @{section}
      A=M
      M=D
    """
    return ret.splitlines()

  ret = []
  #save D into @R14
  ret.append("@R14")
  ret.append("M=D")
  
  #if index is higher we need to add arg and section
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
  
  #retrieve value into D from @R14
  ret.append("@R14")
  ret.append("D=M") 

  #store D into memory pointed by R13
  ret.append("@R13")
  ret.append("A=M")
  ret.append("M=D")
  
  return ret

"""
 just increment the current value in stack
"""
def cmd_inc():
  ret = """
    @SP
    A=M-1
    M=M+1 //load value from stack and increment 
  """
  return ret.splitlines()


"""
 just decrement the current value in stack
"""
def cmd_dec():
  ret = """
    @SP
    A=M-1
    M=M-1 //load value from stack and decrement directly in mem 
  """
  return ret.splitlines()


def cmd_le(i:int):
  #True = -1 False = 0
  ret = f"""
    @lt.skip.{i}
    D;JLE
    @lt.end.{i}
    D=0;JMP
    (lt.skip.{i})
    D=-1
    (lt.end.{i})
  """
  return cmd_subtract_into_D() + ret.splitlines() + cmd_pushD()


def cmd_ge(i:int):
  #True = -1 False = 0
  ret = f"""
    @gt.skip.{i}
    D;JGE
    @gt.end.{i}
    D=0;JMP
    (gt.skip.{i})
    D=-1
    (gt.end.{i})
  """
  return cmd_subtract_into_D() + ret.splitlines() + cmd_pushD()


##########################################################################################
#    Standard hack commands
##########################################################################################

"""
Pushes the register D into stack and increments the stack
"""
def cmd_pushD():
  ret = '''
    @SP   // get SP
    A=M   // get the pointer 
    M=D   // Add D to stack
    @SP   
    M=M+1 // increment SP
  '''
  return ret.splitlines()


"""
  Stores the value stored into section[arg2] into D register 
"""
def cmd_store_into_D(section:string,arg2:int,source:string):
  
  if section=='static':
    ret = f"""
      @static.{source}.{arg2}
      D=M   //read from static memory to D
    """
    return ret.splitlines()
  
  if section==None: # this is a constant number stored into arg2
    
    ret = f"""
      @{arg2}
      D=A  //load the source value into D
    """
    return ret.splitlines()

  # handling sections temp and pointer
  if section==5 or section==3: #this is the temp and pointer
    if section==3 and arg2>1:
      ret.append("#ERR: invalid index for pointer section only [0;1] allowed")  
    if section==5 and arg2>7:
      ret.append("#ERR: invalid index for temp section only [0;7] allowed")
    
    ret =f"""
      @{section+arg2}  //load {"TEMP" if section==5 else 'POINTER'}[{arg2}]
      D=M
    """
    return ret.splitlines()

  # remaining sections: 'LCL[arg2]','THIS','THAT','ARG[arg2]'  
  if arg2==0:
    ret = f"""
      @{section}
      A=M  //load section[0] into A
      D=M
    """
    return ret.splitlines()
  
  if arg2==1:
    ret = f"""
      @{section}
      A=M+1  //load section[1] into A
      D=M
    """
    return ret.splitlines()
  
  ret = f"""
    @{arg2}
    D=A     // put arg 2 into D
    @{section}
    A=D+M   // add section with arg2
    D=M     // Store section[arg2] into D 
  """
  return ret.splitlines()

def cmd_push(section:string,arg2:int,source:string):
  if section==None: # this is a constant number stored into arg2  
    if arg2 in (-1,0,1): # constant is -1 0 or 1 which can be stored directly
      #this results in less instructions and D is not affected
      ret= f"""
        @SP  // select stack
        A=M  // get the pointer
        M={arg2}
        @SP
        M=M+1 // increment stack
      """ 
      return ret.splitlines()
    
  return cmd_store_into_D(section,arg2,source) + cmd_pushD()


"""
pop segment i
addr ← segmentPointer + i
SP--
RAM[addr] ← RAM[SP]
"""
def cmd_pop(section:string,arg2:int,source:string):
  
  if section=='static':
    ret = f"""
      @SP
      AM=M-1  //decrement SP
      D=M     //extract value from SP into D
      
      @static.{source}.{arg2}
      M=D     //save into static
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
    
  # rest of the sections: 'LCL[arg2]','THIS','THAT','ARG[arg2]'
  #Optimize for zero index
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

  if arg2==1:
    ret = f"""
      @{section}
      D=A+1 // points to the section+1
      @R13   
      M=D // save section[1] into R13
      
      @SP
      AM=M-1
      D=M   // pop the stack into D

      @R13
      A=M
      M=D //store D into memory pointed by R13  
    """
    return ret.splitlines()

  # we need to add section + arg2 
  ret = f"""
    @{arg2}
    D=A   // load arg2 into D
    @{section}
    D=D+A // points to the section+arg2
    @R13   
    M=D // save section[arg2] into R13
    
    @SP
    AM=M-1
    D=M   // pop the stack into D

    @R13
    A=M
    M=D //store D into memory pointed by R13  
  """  
  return ret.splitlines()


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


"""
  Takes the two values from the stack and subtracts them: Stack[top-1] - Stack[top] 
"""
def cmd_subtract_into_D():
  ret = f"""
    @SP
    AM=M-1
    D=M
    @SP
    AM=M-1
    D=M-D
  """
  return ret.splitlines()


def cmd_eq(i:int):
  #True = -1 False = 0
  ret = f"""
    @eq.true.{i}
    D;JEQ
    D=-1
    (eq.true.{i})
    D=!D
  """
  return cmd_subtract_into_D() + ret.splitlines() + cmd_pushD()

def cmd_lt(i:int):
  #True = -1 False = 0
  ret = f"""
    @lt.skip.{i}
    D;JLT
    @lt.end.{i}
    D=0;JMP
    (lt.skip.{i})
    D=-1
    (lt.end.{i})
  """
  return cmd_subtract_into_D() + ret.splitlines() + cmd_pushD()


def cmd_gt(i:int):
  #True = -1 False = 0
  ret = f"""
    @gt.skip.{i}
    D;JGT
    @gt.end.{i}
    D=0;JMP
    (gt.skip.{i})
    D=-1
    (gt.end.{i})
  """
  return cmd_subtract_into_D() + ret.splitlines() + cmd_pushD()

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
store nArgs in R13
store address for fName in R14
store return address in D
(label return address)
"""
def cmd_call(fName:string,nArgs:int,i:int):
  ret =f"""
    @{nArgs}
    D=A
    @R13  //store number of arguments into R13
    M=D
    
    @{fName}
    D=A
    @R14  //store number of arguments into R14
    M=D
    
    @return_from_{fName}_{i}
    D=A

    @global_call
    0;JMP 
    (return_from_{fName}_{i})
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

before calling the following registers needs to be prefilled:
D   = return address
R13 = nArgs
R14 = functionAddress
"""
def cmd_call_global():
  ret=f"""
    (global_call)
    @SP   //push returnAddress stored into D already
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

    
    @5 
    D=A
    @R13    //R13 contains the number of arguments
    D=D+M   //D = 5+nArgs
    @SP
    A=M
    D=A-D   //ARG = SP-5-nArgs   (reposition ARG)
    @ARG
    M=D
        
    @R14     //R14 points to function address
    0;JMP    //jump to function label
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
def cmd_return_global():
  ret = """
    (global_return)
    @LCL  
    D=M
    @R13  //save endFrame-1
    M=D-1
    @5
    A=D-A //calculate LCL-5
    D=M
    @R14  //save return address in R14
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
    0;JMP //jmp to address in R14
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

def cmd_return():
  return cmd_jmp("global_return")

def cmd_jmp(lbl:string):
  ret = f"""
    @{lbl}
    0;JMP
  """
  return ret.splitlines()

def error(list,msg):
  list.append(msg)
  raise Exception(msg)