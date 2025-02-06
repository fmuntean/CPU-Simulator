
from hackCPU import opcode_C


class HackAssembler:
    # list of variables originally containing the registers
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

    # a dictionary of labels initialized with the default labels
    labels = {
    "@SCREEN":16384,
    "@KBD":24576,
    "@SP": 0,
    "@LCL":1,
    "@ARG":2,
    "@THIS":3,
    "@THAT":4
    }

    def listVars(lst):
        lst.write(f"\n{'-'*80}\n")
        lst.write("\t\t\t VARIABLES\n")
        lst.write(f"{'-'*80}\n")
        for i in range(len(HackAssembler.vars)):
            lst.write(f"{i:05d}\t{HackAssembler.vars[i]}\n")

    def listLabels(lst):
        lst.write(f"\n{'-'*80}\n")
        lst.write("\t\t\t LABELS\n")
        lst.write(f"{'-'*80}\n")
        for k,v in HackAssembler.labels.items():
            lst.write(f"{v:05d}\t{k}\n")


    def getOpcodeA(line):
        #check if constant
        if line[1:].isnumeric():
            return int(line[1:])
        #check predefined symbols
        if line in HackAssembler.labels.keys():
            return HackAssembler.labels[line]
    
        for i in range(len(HackAssembler.vars)):
            if HackAssembler.vars[i]==line:
                return i
        #the variable is not found so we add it
        HackAssembler.vars.append(line)
        return len(HackAssembler.vars)-1
  

    #first pass extracts labels only
    def pass1(asm):
        addr = 0
        for line in asm:
            pos = line.find('//')
            l = line.strip() if pos==-1 else line[0:pos].strip()
            if len(l)==0:
                continue
            if l.startswith('('):
                HackAssembler.labels[f"@{l[1:-1]}"]=addr
                continue
            if l.startswith('@'):
                addr+=1
                continue
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
                opcode = HackAssembler.labels[f"@{l[1:-1]}"]
                lst.write(f"{addr:05d}\t{l}\n")
                continue
            if l.startswith('//'):
                lst.write(f"\n\t\t{line}")
                rom.write(line.lstrip())
                continue
            if l.startswith('@'):
                opcode = HackAssembler.getOpcodeA(HackAssembler.cleanComments(l))  
                rom.write(f"0x{opcode:04X}\n")
                lst.write(f"{addr:05d}\t0x{opcode:04X}\t{l}\n")
                addr+=1
            else:
                instr = opcode_C()
                opcode = instr.getOpcode(HackAssembler.cleanComments(l))
                rom.write(f"0x{opcode:04X}\n")
                lst.write(f"{addr:05d}\t0x{opcode:X}\t{l}\n")
                addr+=1
        pass

    def cleanComments(line):
        pos = line.find("//")
        return line if pos==-1 else line[:pos].strip()