"""
 hack CPU assembler
"""


from sys import argv

from hackCPU import opcode_C


vars = [
  "@R0",
  "@R1",
  "@R2",
  "@R3",
  "@R4",
  "@R5",
  "@R6",
  "@R7",
  "@R8",
  "@R9",
  "@R10",
  "@R11",
  "@R12",
  "@R13",
  "@R14",
  "@R15"
]




labels = {
  "@SCREEN":16384,
  "@KBD":24576,
  "@SP": 0,
  "@LCL":1,
  "@ARG":2,
  "@THIS":3,
  "@THAT":4
}

def getOpcodeA(line):
  #check if constant
  if line[1:].isnumeric():
    return int(line[1:])
  #check predefined symbols
  if line in labels.keys():
    return labels[line]
  
  for i in range(len(vars)):
    if vars[i]==line:
      return i
  

#first pass extracts labels and variables 
def pass1(asm):
  addr = 0
  for line in asm:
    pos = line.find('//')
    l = line.strip() if pos==-1 else line[0:pos].strip()
    if len(l)==0:
      continue
    if l.startswith('('):
      labels[f"@{l[1:-1]}"]=addr
      continue
    if l.startswith('@'):
      if l[1:].isnumeric():
        addr+=1
        continue
      if l not in vars:
        vars.append(l)
    addr+=1


def assemble(asm,rom,lst):
  addr=0
  for line in asm:
    l = line.strip()
    if len(l)==0:
      continue
    if l =='\n':
      continue
    if l.startswith('('):
      opcode = labels[f"@{l[1:-1]}"]
      lst.write(f"{addr:04X}\t{l}\n")
      continue
    if l.startswith('//'):
      lst.write(line)
      rom.write(line.lstrip())
      continue
    if l.startswith('@'):
      opcode = getOpcodeA(cleancomments(l))  
      rom.write(f"0x{opcode:04X}\n")
      lst.write(f"{addr:04X}\t0x{opcode:04X}\t{l}\n")
      addr+=1
    else:
      instr = opcode_C()
      opcode = instr.getOpcode(cleancomments(l))
      rom.write(f"0x{opcode:04X}\n")
      lst.write(f"{addr:04X}\t0x{opcode:X}\t{l}\n")
      addr+=1
  pass

def cleancomments(line):
  pos = line.find("//")
  return line if pos==-1 else line[:pos].strip()

if __name__ == '__main__':
  asmFile = "hackCPU/pong.asm" # argv[1]
  #asmFile = "hackCPU/Lab06/Rect.asm"
  asmFile = "hackCPU/hackCPU.asm"
  romFile = asmFile[:-3]+'rom' # replace .asm with .rom
  lstFile = asmFile[:-3]+'lst' # replace .asm with .lst
  with open(asmFile,mode="r") as asm:
    pass1(asm)

  with open(asmFile,mode="r") as asm:
    with open(romFile,mode="w") as rom:
      with open(lstFile,mode="w") as lst:
        assemble(asm,rom,lst)
