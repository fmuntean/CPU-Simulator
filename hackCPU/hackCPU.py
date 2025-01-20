
"""
 hack CPU:

 Uses Harvard architecture with separated instruction and data bus

 It has two 16bit registers: A and D
 two flags: zero (zr flag) or negative (ng flag).
 an 16bit program counter: PC

 https://en.wikipedia.org/wiki/Hack_computer
"""


import pathlib


class hackCPU:
    
  def reset(self):
    self.PC = 0
    self.registers = [0,0] # [A,D]
    self.ng = False
    self.zr = True

  def __init__(self,fetchInstruction,fetchMemory,setMemory):
    self.fetchInstruction = fetchInstruction
    self.fetchMemory = fetchMemory
    self.setMemory = setMemory
    self.reset()

  def A(self):
    return self.registers[0]
  
  def D(self):
    return self.registers[1]
  
  def M(self):
    return self.fetchMemory(self.registers[0])
      
  def setA(self,val):
    self.registers[0] = val
  
  def setD(self,val):
    self.registers[1] = val
  
  def setM(self,val):
    self.setMemory(self.registers[0], val)
    
    
  def step(self):
    op,instr = self.getOpcode(self.PC)
    return op.execute(self,instr)

  def getOpcode(self,addr):
    instr = self.fetchInstruction(addr)
    index = instr >> 15
    op = opcodes[index]
    return op,instr
  
  def getRegisters(self):
    return "|PC:{0:04X}|A:{1:04X}|D:{2:04X}|Z:{3:d}|N:{4:d}|".format(self.PC, self.registers[0], self.registers[1], self.zr, self.ng )



class opcode:

  def __init__(self):
    self.length=1 

  def execute(self):
    cpu.PC+=1
    return True
  
  
    
class opcode_A(opcode):    
  def __init__(self):
    super().__init__()
      
  def execute(self,cpu:hackCPU,instr):
    cpu.PC+=1
    cpu.setA(instr)
    cpu.zr = 1 if instr==0 else 0
    cpu.ng = 0 # the numbers here can't be negative as the first bit is always 0
    return True

  def decode(self,cpu,addr):
    instr = cpu.fetchInstruction(addr)
    return f"@{instr}"
  
  def getText(self,instr):
    return f"@{instr}"

"""
Hack machine language computation function codes and assembly language mnemonics
a	c1	c2	c3	c4	c5	c6	ALU Output: f(x,y)	Mnemonic
0	1	0	1	0	1	0	Outputs 0; ignores all operands	0
0	1	1	1	1	1	1	Outputs 1; ignores all operands	1
0	1	1	1	0	1	0	Outputs -1; ignores all operands	-1
0	0	0	1	1	0	0	Outputs D; ignores A and M	D
0	1	1	0	0	0	0	Outputs A; ignores D and M	A
1	1	1	0	0	0	0	Outputs M; ignores D and A	M
0	0	0	1	1	0	1	Outputs bitwise negation of D; ignores A and M	!D
0	1	1	0	0	0	1	Outputs bitwise negation of A; ignores D and M	!A
1	1	1	0	0	0	1	Outputs bitwise negation of M; ignores D and A	!M
0	0	0	1	1	1	1	Outputs 2's complement negative of D; ignores A and M	-D
0	1	1	0	0	1	1	Outputs 2's complement negative of A; ignores D and M	-A
1	1	1	0	0	1	1	Outputs 2's complement negative of M; ignores D and A	-M
0	0	1	1	1	1	1	Outputs D + 1 (increments D); ignores A and M	D+1
0	1	1	0	1	1	1	Outputs A + 1 (increments A); ignores D and M	A+1
1	1	1	0	1	1	1	Outputs M + 1 (increments M); ignores D and A	M+1
0	0	0	1	1	1	0	Outputs D - 1 (decrements D); ignores A and M	D-1
0	1	1	0	0	1	0	Outputs A - 1 (decrements A); ignores D and M	A-1
1	1	1	0	0	1	0	Returns M-1 (decrements M); ignores D and A	M-1
0	0	0	0	0	1	0	Outputs D + A; ignores M	D+A
1	0	0	0	0	1	0	Outputs D + M; ignores A	D+M
0	0	1	0	0	1	1	Outputs D - A; ignores M	D-A
1	0	1	0	0	1	1	Outputs D - M; ignores A	D-M
0	0	0	0	1	1	1	Outputs A - D; ignores M	A-D
1	0	0	0	1	1	1	Outputs M - D; ignores A	M-D
0	0	0	0	0	0	0	Outputs bitwise logical And of D and A; ignores M	D&A
1	0	0	0	0	0	0	Outputs bitwise logical And of D and M; ignores A	D&M
0	0	1	0	1	0	1	Outputs bitwise logical Or of D and A; ignores M	D|A
1	0	1	0	1	0	1	Outputs bitwise logical Or of D and M; ignores A	D|M
"""
ALU = {
  0b0101010: lambda cpu: 0,                          #0
  0b0111111: lambda cpu: 1,                          #1
  0b0111010: lambda cpu: -1 & 0xFFFF,                #-1
  0b0001100: lambda cpu: cpu.D(),                    #D
  0b0110000: lambda cpu: cpu.A(),                    #A
  0b0001101: lambda cpu: ~cpu.D() & 0xFFFF,          #!D
  0b0110001: lambda cpu: ~cpu.A() & 0xFFFF,          #!A
  0b0001111: lambda cpu: -cpu.D() & 0xFFFF,          #-D
  0b0110011: lambda cpu: -cpu.A() & 0xFFFF,          #-A
  0b0011111: lambda cpu: cpu.D()+1 & 0xFFFF,         #D+1
  0b0110111: lambda cpu: cpu.A()+1 & 0xFFFF,         #A+1
  0b0001110: lambda cpu: cpu.D()-1 & 0xFFFF,         #D-1
  0b0110010: lambda cpu: cpu.A()-1 & 0xFFFF,         #A-1
  0b0000010: lambda cpu: cpu.D()+cpu.A() & 0xFFFF,   #D+A
  0b0010011: lambda cpu: cpu.D()-cpu.A() & 0xFFFF,   #D-A
  0b0000111: lambda cpu: cpu.A()-cpu.D() & 0xFFFF,   #A-D
  0b0000000: lambda cpu: cpu.D()&cpu.A() ,           #D&A
  0b0000000: lambda cpu: cpu.D()&cpu.A() ,           #D&A
  0b0010101: lambda cpu: cpu.D()|cpu.A() ,           #D|A

  0b1110000: lambda cpu: cpu.M(),                    #M
  0b1110001: lambda cpu: ~cpu.M() & 0xFFFF,          #!M
  0b1110011: lambda cpu: -cpu.M() & 0xFFFF,          #-M
  0b1110111: lambda cpu: cpu.M()+1 & 0xFFFF,         #M+1
  0b1110010: lambda cpu: cpu.M()-1 & 0xFFFF,         #M-1
  0b1000010: lambda cpu: cpu.D()+cpu.M() & 0xFFFF,   #D+M
  0b1010011: lambda cpu: cpu.D()-cpu.M() & 0xFFFF,   #D-M
  0b1000111: lambda cpu: cpu.M()-cpu.D() & 0xFFFF,   #M-D
  0b1000000: lambda cpu: cpu.D()&cpu.M(),            #D&M
  0b1010101: lambda cpu: cpu.D()|cpu.M()             #D|M
}


"""
Hack machine language branch condition codes and assembly language mnemonics
j1	j2	j3	Branch if	Mnemonic
0	0	0	No branch	none
0	0	1	Output greater than 0	JGT
0	1	0	Output equals 0	JEQ
0	1	1	Output greater than or equal 0	JGE
1	0	0	Output less than 0	JLT
1	0	1	Output not equal 0	JNE
1	1	0	Output less than or equal 0	JLE
1	1	1	Unconditional branch	JMP
"""
jumps = {
  0b000: lambda cpu: cpu.PC+1,                                         #no jump
  0b001: lambda cpu: cpu.A() if cpu.zr==0 and cpu.ng==0  else cpu.PC+1,  #JGT
  0b010: lambda cpu: cpu.A() if cpu.zr==1 else cpu.PC+1,               #JEQ
  0b011: lambda cpu: cpu.A() if cpu.ng==0 else cpu.PC+1,               #JGE
  0b100: lambda cpu: cpu.A() if cpu.ng==1 else cpu.PC+1,               #JLT
  0b101: lambda cpu: cpu.A() if cpu.zr==0 else cpu.PC+1,               #JNE
  0b110: lambda cpu: cpu.A() if cpu.zr==1 or cpu.ng==1 else cpu.PC+1,   #JLE
  0b111: lambda cpu: cpu.A()                                           #JMP
}

class opcode_C(opcode):
  def __init__(self):
    super().__init__()
  
  def extract(instr):
    dest = (instr >> 3) & 0x07 # extract d1d2d3
    jump = (instr & 0x07) # extract j1j2j3
    comp = (instr >> 6) & 0x7F # extract a c1c2c3c4c5c6

    return (dest,jump,comp)
  
  # dest=comp;jump
  # 111a c1c2c3c4 c5c6d1d2 d3j1j2j3
  def execute(self,cpu:hackCPU,instr):
    dest,jump,comp = opcode_C.extract(instr)

    val = ALU[comp](cpu) # execute the ALU instruction
    cpu.zr = 1 if val==0 else 0
    cpu.ng = (val >> 15) & 0x01

    cpu.PC = jumps[jump](cpu)
    
    if dest & 0b001: # store into M
      cpu.setM(val)
    if dest & 0b010: # store into D
      cpu.setD(val)
    if dest & 0b100: # store into A
      cpu.setA(val)         

    
    
    return True

  def decode(self,cpu,addr):
    instr = cpu.fetchInstruction(addr)
    return self.getText(instr)
  

  # dest=comp;jump
  def getText(self,instr):
    dest,jump,comp = opcode_C.extract(instr)
    return f"{destText[dest]}{compText[comp]}{jmpText[jump]}"
  
  # 111a c1c2c3c4 c5c6d1d2 d3j1j2j3
  def getOpcode(self,text):
    # dest=comp;jmp
    del1 = text.find('=')
    del2 = text.find(';')
    dest = text[0 : del1+1] if del1>0 else ""
    jmp  = text[del2 : ] if del2>0 else ""
    comp = text[del1+1 : del2] if del2>0 else text[del1+1:]
    
    ret = 0xE000 | get_index_by_value(jmpText,jmp) | (get_index_by_value(destText,dest)<<3) | (get_index_by_value(compText,comp)<<6)
    return ret

def get_index_by_value(my_dict, value):
  for index, (key, val) in enumerate(my_dict.items()):
    if val == value:
        return key
  return None  # Value not found

jmpText={
  0:"",
  1:";JGT",
  2:";JEQ",
  3:";JGE",
  4:";JLT",
  5:";JNE",
  6:";JLE",
  7:";JMP"
}


destText = {
  0:"",
  1:"M=",
  2:"D=",
  3:"MD=",
  4:"A=",
  5:"AM=",
  6:"AD=",
  7:"AMD="
}

compText = {
  0b0101010: "0",
  0b0111111: "1",
  0b0111010: "-1",
  0b0001100: "D",
  0b0110000: "A",
  0b0001101: "!D",
  0b0110001: "!A",
  0b0001111: "-D",
  0b0110011: "-A",
  0b0011111: "D+1",
  0b0110111: "A+1",
  0b0001110: "D-1",
  0b0110010: "A-1",
  0b0000010: "D+A",
  0b0010011: "D-A",
  0b0000111: "A-D",
  0b0000000: "D&A",
  0b0010101: "D|A",

  0b1110000: "M",
  0b1110001: "!M",
  0b1110011: "-M",
  0b1110111: "M+1",
  0b1110010: "M-1",
  0b1000010: "D+M",
  0b1010011: "D-M",
  0b1000111: "M-D",
  0b1000000: "D&M",
  0b1010101: "D|M"
}

opcodes = [
    opcode_A(),
    opcode_C() 
]



if __name__ == '__main__':
  mem = [0]*0x8000
  def fetchMem(addr):
      return mem[addr % 0x7FFF]
  
  def setMem(addr,val):
    mem[addr % 0x7FFF]=val
  
  cpu = hackCPU(fetchMem,fetchMem,setMem)
  cpu.reset()
  cpu.setD(321)

  asmFile = __file__[:-2]+'asm'
  lstFile = __file__[:-2]+'lst'
  with open(lstFile,mode='w') as lst:
    with open(asmFile,mode="w") as asm:
      asm.write("//hackCPU instructions test\n\n")

      op=opcode_A()
      asm.write(f"{op.getText(123)}\n")
      op.execute(cpu,123)

      lst.write(f"{op.getText(123):12s}\t{cpu.getRegisters()}\n")

      op=opcode_C()
      for jump in range(8):
        for dest in range(1,8):
          for comp in ALU.keys():      
            # 111a c1c2c3c4 c5c6d1d2 d3j1j2j3
            instr = 0x8000 | (comp<<6) | (dest<<3) | jump
            asm.write(f"{op.getText(instr)}\n")
            print(f"{instr:X} => {op.getText(instr )}")
            op.execute(cpu,instr)
            lst.write(f"{op.getText(instr):12s}\t{cpu.getRegisters()}\tM=0x{fetchMem(cpu.A()):04X}\n")