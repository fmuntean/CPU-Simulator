# Motorola MC6800 / MC6802 CPU simulator
# opcodes implementation from: 
#   http://www.8bit-era.cz/6800.html
#   http://www.bitsavers.org/components/motorola/6800/Motorola_M6800_Programming_Reference_Manual_M68PRM(D)_Nov76.pdf

# Registers:
#    A,B	Accumulator     8bit
#    IX	    Index register  16bit
#    PC	    Program Counter 16bit
#    SP	    Stack Pointer   16bit
#    SR	    Status register 8bit
#    
# Status Register:
#   H = Half-Cary Set when cary from b3 to b4 affected by ADD,ABA,ADC
#   I = interrupt mask
#   N = negative set when bit 7 is 1
#   Z = zero (set when result is zero)
#   V = Overflow (set when operation overflow)
#   C = Carry (set when was a cary from bit7)

from mypy_extensions import i16


class MC6800:
    # Reset Pointer                  = 0xFFFF-1
    # Non Maskable Interrupt Pointer = 0xFFFF-3
    # Software Interrupt Pointer     = 0xFFFF-5
    # Internal Interrupt Pointer     = 0xFFFF-7



    def __init__(self,fetchMemory=None,setMemory=None):
        self.fetchInstruction = fetchMemory # the same memory is shared between code and data
        self.fetchMemory = fetchMemory
        self.setMemory = setMemory
        if fetchMemory is not None:
            self.reset()

    def setMemoryHandlers(self,fetchMemory,setMemory):
        self.fetchMemory = fetchMemory
        self.setMemory = setMemory
        self.reset()

    def reset(self)->None:
        self.PC : i16 = 0xFFFF if self.fetchMemory is None else self.fetchMemory(0xFFFE)*256+self.fetchMemory(0xFFFF)
        self.A  : i16 = 0
        self.B  : i16 = 0
        self.IX : i16 = 0
        self.SP : i16 = 0
        self.SR : i16 = 0xC0 # highest two bits are always 11 H I N Z V C

    def getRegister(self, reg:str)->i16:
        match reg:
            case "A":
                return self.A
            case "B":
                return self.B
            case "IX":
                return self.IX
            case "SP":
                return self.SP
            case "SR":
                return self.SR
            case "PC":
                return self.PC
        
    def setRegister(self, reg:str, val:i16)->None:
        match reg:
            case "A":
                self.A = val & 0xFF
            case "B":
                self.B = val & 0xFF
            case "IX":
                self.IX = val & 0xFFFF
            case "SP":
                self.SP = val & 0xFFFF
            case "SR":
                self.SR = (val | 0xC0) & 0xFF
            case "PC":
                self.PC = val & 0xFFFF

    def getFlagH(self)->i16:
        return self.SR & 0x20

    def setFlagC(self,regOut):
        self.SR = self.SR | 1 if (regOut<0 or regOut>255) else self.SR & 0xFE

    def getFlagV(self):
        return self.SR & 0x02

    def setFlagV(self,reg1in,reg2in,regOut):
        v = ((((reg1in & 0x80) == 0x80) & ((reg2in & 0x80) == 0x80) & ((regOut & 0x80) != 0x80)) #overflow
		| (((reg1in & 0x80) != 0x80) & ((reg2in & 0x80) != 0x80) & ((regOut & 0x80) == 0x80)))  #overflow
        self.SR = self.SR | 2 if (v) else self.SR & 0xFD   

    def resetFlagV(self):
        self.SR = self.SR & 0xFD

    def setFlagZ(self,reg1in):
        self.SR = self.SR | 4 if (reg1in ==0) else self.SR & 0xFB
    
    def setFlagN(self,regOut):
        n = (regOut & 0x80) > 0
        self.SR = self.SR | 8 if (n) else self.SR & 0xF7
    
    def setFlagI(self,i):
        self.SR = self.SR | 16 if (i) else self.SR & 0xEF
    
    def setFlagH(self,reg1in, reg2in, regOut):
        h = ((reg1in & reg2in ) | ((reg1in | reg2in) & (0xFF - regOut)) ) & 8 > 0 
        self.SR = self.SR | 32 if (h) else self.SR & 0xDF

    def setFlagNZ(self, reg1in):
        self.setFlagZ(reg1in)
        self.setFlagN(reg1in)

    def setFlagNZVC(self,reg1in,reg2in,regOut):
        self.setFlagC(regOut)
        self.setFlagV(reg1in,reg2in,regOut)
        self.setFlagZ(regOut)
        self.setFlagN(regOut)

    def setFlagHNZVC(self,reg1in,reg2in,regOut):
        self.setFlagC(regOut)
        self.setFlagV(reg1in,reg2in,regOut)
        self.setFlagZ(regOut)
        self.setFlagN(regOut)
        self.setFlagH(reg1in,reg2in,regOut)


    def resetFlagC(self):
        self.SR & 0xFE

    def getFlagC(self):
        return self.SR & 1
    
    def getFlagZ(self):
        return self.SR & 4

    def getFlagN(self):
        return self.SR & 0x08
        
    def step(self):
        ops = list(filter(lambda x: x.code == self.fetchMemory(self.PC & 0xFFFF), opcodes))
        op = ops[0] if ops else None
        return op.execute(self) if op else False

    def getOpcode(self,index):
        ops = list(filter(lambda x: x.code == self.fetchMemory(index), opcodes)) 
        op = ops[0] if ops else None
        return op,None
    
    def getRegisters(self):
        # status register SR highest two bits are always 11 H I N Z V C
        return f"|PC:{self.PC:04X}|A:{self.A:02X}|B:{self.B:02X}|IX:{self.IX:04X}|SP:{self.SP:04X}||H{self.SR>>5&0x01} I{self.SR>>4&0x01} N{self.SR>>3&0x01} Z{self.SR>>2&0x01} V{self.SR>>1&0x01} C{self.SR&0x01}"



class opcode:
    length= 0
    code = 0
    text = ""
    type= "INH" # inherent
    reg = ""
   
    def __init__(self,code,length, text, type, reg):
        self.code = code
        self.length = length 
        self.text = text
        self.type = type
        self.reg = reg

    def getHex(self):
        ret = f"{self.code:02X}"
        return ret

    def getText(self):
        return self.text

    def getRelativeAddress(self, pc, rel):
        addr = pc + 2 -(0xFF - rel)-1 if rel & 0x80 else rel+pc+2
        return addr

    def decode(self,cpu,address):
        ret = self.text
        if self.length>1: #it is a two byte instruction
            match self.type:
                case "IMM":
                    if self.reg in ['IX','SP','PC']:
                        ret+=f" {cpu.fetchMemory(address+1,True):02X}{cpu.fetchMemory(address+2,True):02X}"  # number16
                    elif self.reg !='':    
                        ret+=f" {self.reg},#${cpu.fetchMemory(address+1,True):02X}"
                    else:
                        ret+=f",{cpu.fetchMemory(address+1,True):02X}"  # number8
                case "DIR":
                    if self.reg in ['IX','SP','PC']:
                        addr = cpu.fetchMemory(address+1,True)
                        ret+=f" [{addr:02X}] ({(cpu.fetchMemory(addr,True)*256+cpu.fetchMemory(addr+1,True)):04X})" #[addr16]
                    else:
                        addr=cpu.fetchMemory(address+1,True)
                        ret+=f" {self.reg},[{addr:02X}] ({cpu.fetchMemory(addr,True):02X})" # [addr8]
                case "IND":
                    addr = cpu.fetchMemory(address+1,True)
                    ret+=f" {self.reg},[IX+{addr:02X}] [{(addr+cpu.IX):04X}] ({(cpu.fetchMemory(addr+cpu.IX,True)):02X})"  # [addr8+IX]
                case "EXT":
                    if self.reg in ['IX','SP','PC']:
                        addr = cpu.fetchMemory(address+1,True)*256+cpu.fetchMemory(address+2,True)
                        ret+=f" [{addr:04X}] ({(cpu.fetchMemory(addr,True)*256+cpu.fetchMemory(addr+1,True)):04X})" #[addr16]
                    elif self.reg:
                        addr = (cpu.fetchMemory(address+1,True)*256+cpu.fetchMemory(address+2,True))
                        ret+=f" {self.reg},[{addr:04X}] ({cpu.fetchMemory(addr,True):02X})" #[addr16]
                    else:
                        addr = (cpu.fetchMemory(address+1,True)*256+cpu.fetchMemory(address+2,True))
                        ret+=f" [{addr:04X}] ({cpu.fetchMemory(addr,True):02X})" #addr16
                case "REL":
                    ret+=f" {cpu.fetchMemory(address+1,True):02X} ({self.getRelativeAddress(cpu.PC, cpu.fetchMemory(address+1,True)):04X})"
                case "IDX":
                    if self.reg in ['IX','SP','PC']:
                        addr = cpu.fetchMemory(address+1,True)
                        ret+=f" [IX+{addr:02X}] [{(addr+cpu.IX):04X}] ({(cpu.fetchMemory(addr+cpu.IX,True)*256+cpu.fetchMemory(addr+cpu.IX+1,True)):04X})" #[addr16]
                    elif self.reg:
                        addr = cpu.fetchMemory(address+1,True)
                        ret+=f" {self.reg},[IX+{addr:02X}] [{(addr+cpu.IX):04X}] ({(cpu.fetchMemory(addr+cpu.IX,True)):02X})"
                    else:
                        addr = cpu.fetchMemory(address+1,True)
                        ret+=f" [IX+{addr:02X}] [{(addr+cpu.IX):04X}] ({(cpu.fetchMemory(addr+cpu.IX,True)):02X})"
        else: #it is a one byte instruction
            if self.reg:
                ret+=f" {self.reg}"
        return ret



#--- ABA : Add B to A
class opcode_ABA(opcode):
    def __init__(self):
        super().__init__(0x1B,1,"ABA","ACC","") #A = A+B

    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
        
    def execute(self,cpu):
        R = (cpu.A+cpu.B)
        cpu.setFlagHNZVC(cpu.A,cpu.B,R)
        cpu.A = R & 0xFF
        cpu.PC+=1
        return True


#--- ADC : Add contents of Memory + Carry Flag to Accumulator
class opcode_ADC(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)

    def execute(self,cpu):
        match self.type:
            case "IMM":
                val = cpu.fetchMemory(cpu.PC+1)
            case "DIR":
                addr8 = cpu.fetchMemory(cpu.PC+1)
                val = cpu.fetchMemory(addr8)
            case "IDX":
                addr8 = cpu.fetchMemory(cpu.PC+1)
                val = cpu.fetchMemory(addr8+cpu.IX)
            case "EXT":
                addr16 = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr16)
        c = cpu.getFlagC()
        r = cpu.getRegister(self.reg)
        ret = r + val + c
        cpu.setFlagHNZVC(r,val,ret)
        cpu.setRegister(self.reg, ret % 256)
        cpu.PC+=self.length
        return True


#--- ADD : Add Memory contents to the Accumulator
class opcode_ADD(opcode):    
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "IMM":
                val = cpu.fetchMemory(cpu.PC+1)
            case "DIR":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1))
            case "IDX":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1)+cpu.IX)
            case "EXT":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2))
        
        r = cpu.getRegister(self.reg)
        ret = r + val
        cpu.setFlagHNZVC(r,val,ret)
        cpu.setRegister(self.reg,ret % 256)
        cpu.PC+=self.length
        return True


#---- Memory contents AND the Accumulator to the Accumulator --#
class opcode_AND(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "IMM":
                val = cpu.fetchMemory(cpu.PC+1)
            case "DIR":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1))
            case "IDX":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1)+cpu.IX)
            case "EXT":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2))
        
        r = cpu.getRegister(self.reg)
        ret = r & val
        cpu.resetFlagV()
        cpu.setFlagZ(ret)
        cpu.setFlagC(ret)
        cpu.setRegister(self.reg,ret % 256)
        cpu.PC+=self.length
        return True


#--- Arithmetic Shift Left. Bit 0 is set to 0. (multiplying by two) --#
class opcode_ASL(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "ACC":
                val = cpu.getRegister(self.reg)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
                val = cpu.fetchMemory(addr)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr)
        
        ret = val<<1
        cpu.setFlagN(ret)
        cpu.setFlagZ(ret)
        cpu.setFlagC(ret)
        V = (cpu.SR & 0x01) ^ (cpu.SR>>3 & 0x01) 
        cpu.SR = cpu.SR | 0x02 if (V==1) else cpu.SR & 0xFD
        match self.type:
            case "ACC":
                cpu.setRegister(self.reg,ret % 256)
            case "IDX":
                cpu.setMemory(addr,ret & 0xFF)
            case "EXT":
                cpu.setMemory(addr,ret & 0xFF)
        cpu.PC+=self.length
        return True


#----- Arithmetic Shift Right. Bit 7 stays the same. ---#
class opcode_ASR(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "ACC":
                val = cpu.getRegister(self.reg)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
                val = cpu.fetchMemory(addr)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr)
        
        ret = (256*(val&1)) + (val&0x80) + (val>>1)
        cpu.setFlagN(ret)
        cpu.setFlagZ(ret)
        cpu.setFlagC(ret)
        V = (cpu.SR & 0x01) ^ (cpu.SR>>3 & 0x01) 
        cpu.SR = cpu.SR | 0x02 if (V==1) else cpu.SR & 0xFD
        match self.type:
            case "ACC":
                cpu.setRegister(self.reg,ret % 256)
            case "IDX":
                cpu.setMemory(addr,ret & 0xFF)
            case "EXT":
                cpu.setMemory(addr,ret & 0xFF)
        cpu.PC+=self.length
        return True


#---- Branch if carry clear ----#
class opcode_BCC(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        if (cpu.getFlagC()==0):
            rel = cpu.fetchMemory(cpu.PC+1)
            rel = -(0xFF - rel)-1 if rel & 0x80 else rel
            cpu.PC+=rel+2
        else:
            cpu.PC+=2
        return True


#--- Branch if carry set ---#
class opcode_BCS(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        if (cpu.getFlagC()>0):
            rel = cpu.fetchMemory(cpu.PC+1)
            rel = -(0xFF - rel)-1 if rel & 0x80 else rel
            cpu.PC+=rel+2
        else:
            cpu.PC+=2
        return True


#--- 	Branch if equal to zero ----#
class opcode_BEQ(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        if (cpu.getFlagZ()>0):
            rel = cpu.fetchMemory(cpu.PC+1)
            rel = -(0xFF - rel)-1 if rel & 0x80 else rel
            cpu.PC+=rel+2
        else:
            cpu.PC+=2
        return True


#--- Branch if greater than or equal to zero ---#
# Causes a branch if (N is set and V is set) OR (N is clear and V is clear).
class opcode_BGE(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        if ((cpu.SR & 0x0A)==0x0A  |  (cpu.SR & 0x0A)==0x00 ):
            rel = cpu.fetchMemory(cpu.PC+1)
            rel = -(0xFF - rel)-1 if rel & 0x80 else rel
            cpu.PC+=rel+2
        else:
            cpu.PC+=2
        return True


#---- Branch if greater than zero ----#
#Causes a branch if [Z is clear] AND [(N is set and V is set) OR (N is clear and V is clear)].
class opcode_BGT(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        if (cpu.getFlagZ()==0 & ((cpu.SR & 0x0A)==0x0A  |  (cpu.SR & 0x0A)==0x00 )):
            rel = cpu.fetchMemory(cpu.PC+1)
            rel = -(0xFF - rel)-1 if rel & 0x80 else rel
            cpu.PC+=rel+2
        else:
            cpu.PC+=2
        return True


#---- Branch if Accumulator contents higher than comparand -----#
# Causes a branch if (C is clear) AND (Z is clear).
class opcode_BHI(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        if ( (cpu.SR & 0x05)==0x00 ):
            rel = cpu.fetchMemory(cpu.PC+1)
            rel = -(0xFF - rel)-1 if rel & 0x80 else rel
            cpu.PC+=rel+2
        else:
            cpu.PC+=2
        return True
    

#-----BIT Memory contents AND the Accumulator, but only Status register is affected. ---#
# Performs the logical"AND" comparison of the contents of ACCX and the contents
#of M and modifies condition codes accordingly. Neither the contents of ACCX or M
#operands are affected. (Each bit of the result of the "AND" would be the logical
#"AND" of the corresponding bits of M and ACCX.)
class opcode_BIT(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "IMM":
                val = cpu.getRegister(self.reg)
            case "DIR":
                val = cpu.fetchMemory(cpu.PC+1)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
                val = cpu.fetchMemory(addr)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr)
        reg = cpu.getRegister(self.reg)
        ret = reg & val
        cpu.setFlagN(ret)
        cpu.setFlagZ(ret)
        cpu.resetFlagV()
        cpu.setRegister(self.reg,ret % 256)
        cpu.PC+=self.length
        return True


#---- BLE Branch if less than or equal to zero ---#
# Causes a branch if [Z is set] OR [(N is set and V is clear) OR (N is clear and V is set)].
class opcode_BLE(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        if ( (cpu.SR & 0x04)==0x04 | (cpu.SR & 0x0A) in [0x08, 0x02] ):
            rel = cpu.fetchMemory(cpu.PC+1)
            rel = -(0xFF - rel)-1 if rel & 0x80 else rel
            cpu.PC+=rel+2
        else:
            cpu.PC+=2
        return True


#---- BLS: Branch if Accumulator contents less than or same as comparand ----#
# Causes a branch if (C is set) OR (Z is set).
class opcode_BLS(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        if ( cpu.getFlagC() | cpu.getFlagZ() ):
            rel = cpu.fetchMemory(cpu.PC+1)
            rel = -(0xFF - rel)-1 if rel & 0x80 else rel
            cpu.PC+=rel+2
        else:
            cpu.PC+=2
        return True


#---- BLT: Branch if less than zero ---#
# Causes a branch if (N is set and V is clear) OR (N is clear and V is set).
class opcode_BLT(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        if ( (cpu.SR & 0x0A) in [0x08, 0x02] ):
            rel = cpu.fetchMemory(cpu.PC+1)
            rel = -(0xFF - rel)-1 if rel & 0x80 else rel
            cpu.PC+=rel+2
        else:
            cpu.PC+=2
        return True


#---- BMI: Branch if minus -----#
# Tests the state of the N bit and causes a branch if N is set.
class opcode_BMI(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        if ( cpu.getFlagN() ):
            rel = cpu.fetchMemory(cpu.PC+1)
            rel = -(0xFF - rel)-1 if rel & 0x80 else rel
            cpu.PC+=rel+2
        else:
            cpu.PC+=2
        return True   


#--- BNE: 	Branch if not equal to zero
# Tests the state of the Z bit and causes a branch if the Z bit is clear.
class opcode_BNE(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        if ( cpu.getFlagZ() == 0 ):
            rel = cpu.fetchMemory(cpu.PC+1)
            rel = -(0xFF - rel)-1 if rel & 0x80 else rel
            cpu.PC+=rel+2
        else:
            cpu.PC+=2
        return True     


# BPL: Branch if plus
# Tests the state of the N bit and causes a branch if N is clear.
class opcode_BPL(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        if ( cpu.getFlagN() == 0 ):
            rel = cpu.fetchMemory(cpu.PC+1)
            if rel & 0x80:
                rel = -(0xFF - rel)-1
            cpu.PC+=rel+2
        else:
            cpu.PC+=2
        return True 


# BRA: Unconditional branch relative to present Program Counter contents
class opcode_BRA(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        rel = cpu.fetchMemory(cpu.PC+1)
        rel = -(0xFF - rel)-1 if rel & 0x80 else rel
        cpu.PC+=rel+2
        return True 


# BSR: Unconditional branch to subroutine located relative to present Program Counter contents.   
# The program counter is incremented by 2. The less significant byte of the contents
# of the program counter is pushed into the stack. The stack pointer is then
# decremented (by 1). The more significant byte of the contents of the program
# counter is then pushed into the stack. The stack pointer is again decremented (by 1). 
# A branch then occurs to the location specified by the program.
class opcode_BSR(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        rel = cpu.fetchMemory(cpu.PC+1)
        rel = -(0xFF - rel)-1 if rel & 0x80 else rel
        cpu.PC+=2
        cpu.setMemory(cpu.SP,cpu.PC & 0xFF)
        cpu.SP-=1
        cpu.setMemory(cpu.SP,cpu.PC>>8 & 0xFF)
        cpu.SP-=1
        cpu.PC+=rel
        return True 


#---  BVC Branch if Overflow Clear
#Operation: PC ~ (PC) + 0002 + Rei if (V) = 0
#Description: Tests the state of the V bit and causes a branch if the V bit is clear
class opcode_BVC(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        if ( cpu.getFlagV() == 0 ):
            rel = cpu.fetchMemory(cpu.PC+1)
            rel = -(0xFF - rel)-1 if rel & 0x80 else rel
            cpu.PC+=rel+2
        else:
            cpu.PC+=2
        return True 


#---- BVS Branch if overflow set
class opcode_BVS(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        if ( cpu.getFlagV() ):
            rel = cpu.fetchMemory(cpu.PC+1)
            rel = -(0xFF - rel)-1 if rel & 0x80 else rel
            cpu.PC+=rel+2
        else:
            cpu.PC+=2
        return True    


# CBA: Compares the contents ofACCA and the contents ofACCB and sets the condition
# codes, which may be used for arithmetic and logical conditional branches. 
# Both operands are unaffected
class opcode_CBA(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        reg1 = cpu.A
        reg2 = cpu.B
        r = reg1 - reg2
        cpu.setFlagNZVC(reg1,reg2,r)
        cpu.PC+=1
        return True    


#--- CLC : Clear the Carry Flag
class opcode_CLC(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        cpu.setFlagC(0)
        cpu.PC+=1
        return True 


#--- CLI : Clear the Interrupt Flag (Enable Interrupts)
class opcode_CLI(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        cpu.SR & 0xEF
        cpu.PC+=1
        return True


#--- CLR : Clear Accumulator or the Memory location
class opcode_CLR(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "ACC":
                cpu.setRegister(self.reg, 0)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
                cpu.setMemory(addr,0)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                cpu.setMemory(addr,0)
        cpu.SR = cpu.SR & 0xF0
        cpu.setFlagZ(0)
        cpu.PC+=self.length
        return True


#--- CLV : Clear the Overflow flag
class opcode_CLV(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        cpu.SR & 0xFD
        cpu.PC+=1
        return True


# CMP : Compare the contents of Memory and Accumulator. Only the Status register is affected.
class opcode_CMP(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "IMM":
                val = cpu.fetchMemory(cpu.PC+1)
            case "DIR":
                addr = cpu.fetchMemory(cpu.PC+1)
                val = cpu.fetchMemory(addr)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
                val = cpu.fetchMemory(addr)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr)
        reg = cpu.getRegister(self.reg)
        
        ret = reg - val
        cpu.setFlagNZVC(reg, val, ret)
        
        cpu.PC+=self.length
        return True


# COM : Complement the Accumulator
class opcode_COM(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "ACC":
                val = cpu.getRegister(self.reg)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
                val = cpu.fetchMemory(addr)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr)
        ret = 0xFF - val 
        cpu.setFlagN(ret)
        cpu.setFlagZ(ret)
        cpu.resetFlagV()
        cpu.setFlagC(256)
        match self.type:
            case "ACC":
                cpu.setRegister(self.reg ,ret)
            case "IDX":
                cpu.setMemory(addr, ret)
            case "EXT":
                cpu.setMemory(addr, ret)
        cpu.PC+=self.length
        return True
 

#--- CPX: Compare the contents of Memory to the Index Register
class opcode_CPX(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "DIR":
                addr = cpu.fetchMemory(cpu.PC+1)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
            case "IMM":
                addr = cpu.PC+1
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
        val = cpu.fetchMemory(addr)*256+cpu.fetchMemory(addr+1)
        r = cpu.IX
        ret = r - val
        cpu.setFlagN(ret>>8)
        cpu.setFlagZ(ret)
        cpu.setFlagV(r,val,ret)
        cpu.PC+=self.length
        return True


#---- DAA Decimal Adjust Accumulator A
# Adds hexadecimal numbers 00, 06, 60, or 66 to ACCA, and may also set the carry bit.
"""
State of |          |           |          |Number |State of
C-bit    | Upper    |Initial    | Lower    | Added | C-bit
before   |Half-byte |Half-carry | to ACCA  | after |
DAA      |(bits 4-7)| H-bit     |(bits 0-3)| byDAA | DAA
----------------------------------------------------------
0        | 0-9      | 0         |    0-9   | 00    |  0
0        | 0-8      | 0         |    A-F   | 06    |  0
0        | 0-9      | 1         |    0-3   | 06    |  0
0        | A-F      | 0         |    0-9   | 60    |  1
0        | 9-F      | 0         |    A-F   | 66    |  1
0        | A-F      | 1         |    0-3   | 66    |  1
1        | 0-2      | 0         |    0-9   | 60    |  1
1        | 0-2      | 0         |    A-F   | 66    |  1
1        | 0-3      | 1         |    0-3   | 66    |  1
"""
class opcode_DAA(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        c = cpu.getFlagC()
        h = cpu.getFlagH()
        upper = cpu.A >> 4
        lower = cpu.A & 0x0F

        #r=cpu.A
        if (c==0 and h==0):
            if (upper<10 and lower<10):
                r=cpu.A
                cpu.setFlagC(0)
            if (upper<9 and lower>9):
                r = cpu.A+0x06
                cpu.setFlagC(0)
            if (upper>9 and lower<10):
                r = cpu.A+0x60
                cpu.setFlagC(256)
            if (upper>8 and lower>9):
                r=cpu.A+0x66
                cpu.setFlagC(256)
        elif c==0 and h!=0:
            if (upper<10 and lower<4):
                r=cpu.A+0x06
                cpu.setFlagC(0)
            if (upper>9 and lower<4):
                r=cpu.A+0x66
                cpu.setFlagC(256)
        elif c!=0 and h==0:
            if (upper<3 and lower<10):
                r=cpu.A+0x60
                cpu.setFlagC(256)
            if (upper<3 and lower>9):
                r = cpu.A+0x66
                cpu.setFlagC(256)
        else: # c==1 and h==1:  
            if (upper<4 and lower<4):
                r = cpu.A+0x66
                cpu.setFlagC(256)

        cpu.setFlagN(r)
        cpu.setFlagZ(r)
        cpu.A = r & 0XFF
        cpu.PC+=1
        return True   


#--- DEC : Subtract one from the contents of ACCX or M
class opcode_DEC(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "ACC":
                val = cpu.getRegister(self.reg)
            case "DIR":
                val = cpu.fetchMemory(cpu.PC+1)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
                val = cpu.fetchMemory(addr)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr)
        ret = val - 1
        cpu.setFlagNZ(ret)
        cpu.SR = cpu.SR | 0x02 if val==0x80 else cpu.SR & 0xFD
        match self.type:
            case "ACC":
                cpu.setRegister(self.reg,ret % 256)
            case "IDX":
                cpu.setMemory(addr,ret & 0xFF)
            case "EXT":
                cpu.setMemory(addr,ret & 0xFF)
        cpu.PC+=self.length
        return True


#--- DES : Decrement the Stack Pointer
class opcode_DES(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        cpu.SP-=1
        cpu.PC+=1
        return True 


class opcode_CLR(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "ACC":
                cpu.setRegister(self.reg, 0)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
                cpu.setMemory(addr,0)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                cpu.setMemory(addr,0)
        cpu.SR = cpu.SR & 0xF0
        cpu.setFlagZ(0)
        cpu.PC+=self.length
        return True


class opcode_CLV(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        cpu.SR & 0xFD
        cpu.PC+=1
        return True


#--- DEX : Decrement the Index Register
class opcode_DEX(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        cpu.IX-=1
        cpu.setFlagZ(cpu.IX)
        cpu.PC+=1
        return True 


#--- EOR : Memory contents EXCLUSIVE OR the Accumulator
class opcode_EOR(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "IMM":
                val = cpu.fetchMemory(cpu.PC+1)
            case "DIR":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1))
            case "IDX":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1)+cpu.IX)
            case "EXT":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2))
        
        r = cpu.getRegister(self.reg)
        ret = r ^ val
        cpu.setFlagN(ret)
        cpu.setFlagZ(ret)
        cpu.resetFlagV()
        cpu.setRegister(self.reg,ret % 256)
        cpu.PC+=self.length
        return True


#--- INC : Increment the Accumulator or the Memory location
class opcode_INC(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "ACC":
                val = cpu.getRegister(self.reg)
            case "DIR":
                val = cpu.fetchMemory(cpu.PC+1)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
                val = cpu.fetchMemory(addr)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr)
        ret = val + 1
        cpu.setFlagNZ(ret)
        cpu.SR = cpu.SR | 0x02 if val==0x7F else cpu.SR & 0xFD
        match self.type:
            case "ACC":
                cpu.setRegister(self.reg,ret % 256)
            case "IDX":
                cpu.setMemory(addr,ret & 0xFF)
            case "EXT":
                cpu.setMemory(addr,ret & 0xFF)
        cpu.PC+=self.length
        return True


#--- INS : Increment the Stack Pointer
class opcode_INS(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        cpu.SP=(cpu.SP+1) & 0xFFFF
        cpu.PC+=1
        return True 


#--- INX : Increment the Index Register
class opcode_INX(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        cpu.IX= (cpu.IX+1) & 0xFFFF
        cpu.setFlagZ(cpu.IX)
        cpu.PC+=1
        return True 


#-- JMP : Jump
class opcode_JMP(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        match self.type:
            case "IDX":
                cpu.PC = cpu.fetchMemory(cpu.PC+1)+cpu.IX
            case "EXT":
                cpu.PC = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
        return True 

    def decode(self,cpu,address):
        ret = self.text
        match self.type:
            case "IDX":
                addr = cpu.fetchMemory(address+1)
                ret+=f" IX+{addr:02X} ({(addr+cpu.IX):04X})" #[addr16]  
            case "EXT":
                ret+=f" {(cpu.fetchMemory(address+1)*256+cpu.fetchMemory(address+2)):04X}" #addr16
        return ret


#--- JSR : Jump to Subroutine
class opcode_JSR(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        pc = cpu.PC+self.length
        cpu.setMemory(cpu.SP, pc & 0xFF)
        cpu.SP-=1
        cpu.setMemory(cpu.SP, pc >> 8)
        cpu.SP-=1
        match self.type:
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1) + cpu.IX
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
        cpu.PC = addr
        return True 

    def decode(self,cpu,address):
        ret = self.text
        match self.type:
            case "IDX":
                addr = cpu.fetchMemory(address+1)
                ret+=f" IX+{addr:02X} ({(addr+cpu.IX):04X})" #[addr16]    
            case "EXT":
                ret+=f" {(cpu.fetchMemory(address+1)*256+cpu.fetchMemory(address+2)):04X}" #addr16
        return ret
    

#--- LDA : Load Accumulator from Memory
class opcode_LDA(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "IMM":
                val = cpu.fetchMemory(cpu.PC+1)
            case "DIR":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1))
            case "IDX":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1)+cpu.IX)
            case "EXT":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2))
        r = cpu.getRegister(self.reg)
        cpu.setFlagN(val)
        cpu.setFlagZ(val)
        cpu.resetFlagV()
        cpu.setRegister(self.reg,val & 0xFF)
        cpu.PC+=self.length
        return True


#--- LDS: Load the Stack Pointer
class opcode_LDS(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "IMM":
                val = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
            case "DIR":
                addr = cpu.fetchMemory(cpu.PC+1)
                val = cpu.fetchMemory(addr)*256+cpu.fetchMemory(addr+1)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
                val = cpu.fetchMemory(addr)*256+cpu.fetchMemory(addr+1)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr)*256+cpu.fetchMemory(addr+1)
        cpu.setFlagN(val)
        cpu.setFlagZ(val)
        cpu.resetFlagV()
        cpu.SP = val
        cpu.PC+=self.length
        return True   


#--- LDX : Load the Index Register
class opcode_LDX(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "IMM":
                val = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
            case "DIR":
                addr = cpu.fetchMemory(cpu.PC+1)
                val = cpu.fetchMemory(addr)*256+cpu.fetchMemory(addr+1)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
                val = cpu.fetchMemory(addr)*256+cpu.fetchMemory(addr+1)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr)*256+cpu.fetchMemory(addr+1)
        cpu.setFlagN(val)
        cpu.setFlagZ(val)
        cpu.resetFlagV()
        cpu.IX = val
        cpu.PC+=self.length
        return True 


#--- LSR : 	Logical Shift Right. Bit 7 is set to 0. (dividing by two)
class opcode_LSR(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "ACC":
                val = cpu.getRegister(self.reg)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
                val = cpu.fetchMemory(addr)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr)
        ret = val>>1
        cpu.setFlagN(0)
        cpu.setFlagZ(ret)
        cpu.SR = cpu.SR | 0x01 if val & 0x01 else cpu.SR & 0xFE # C flag
        V = (cpu.SR & 0x01) ^ (cpu.SR>>3 & 0x01) 
        cpu.SR = cpu.SR | 0x02 if (V==1) else cpu.SR & 0xFD
        match self.type:
            case "ACC":
                cpu.setRegister(self.reg,ret % 256)
            case "IDX":
                cpu.setMemory(addr,ret & 0xFF)
            case "EXT":
                cpu.setMemory(addr,ret & 0xFF)
        cpu.PC+=self.length
        return True


#--- NEG : Negate the Accumulator or memory location
class opcode_NEG(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "ACC":
                val = cpu.getRegister(self.reg)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
                val = cpu.fetchMemory(addr)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr)
        
        ret = 0-val
        cpu.setFlagN(ret)
        cpu.setFlagZ(ret)
        cpu.SR = cpu.SR & 0xFE if val == 0 else cpu.SR | 1  # C flag
        cpu.SR = cpu.SR | 0x02 if val == 0x80 else cpu.SR & 0xFD # V flag
        match self.type:
            case "ACC":
                cpu.setRegister(self.reg,ret % 256)
            case "IDX":
                cpu.setMemory(addr,ret & 0xFF)
            case "EXT":
                cpu.setMemory(addr,ret & 0xFF)
        cpu.PC+=self.length
        return True

#--- NOP : No operation
class opcode_NOP(opcode):    
    def __init__(self):
        super().__init__(0x01,1,"NOP","","")

    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
       
    def execute(self,cpu):
        cpu.PC+=1
        return True 


#--- ORA : OR the Accumulator
class opcode_ORA(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "IMM":
                val = cpu.fetchMemory(cpu.PC+1)
            case "DIR":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1))
            case "IDX":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1)+cpu.IX)
            case "EXT":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2))
        r = cpu.getRegister(self.reg)
        ret = r | val
        cpu.resetFlagV()
        cpu.setFlagZ(ret)
        cpu.setFlagN(ret)
        cpu.setRegister(self.reg,ret % 256)
        cpu.PC+=self.length
        return True
 

#--- PSH : Push Accumulator into stack
class opcode_PSH(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        val = cpu.getRegister(self.reg)
        cpu.setMemory(cpu.SP,val)
        cpu.SP-=1
        cpu.PC+=self.length
        return True 

#--- PUL : Pull accumulator form Stack
class opcode_PUL(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        cpu.SP+=1
        val = cpu.fetchMemory(cpu.SP)
        cpu.setRegister(self.reg,val)
        cpu.PC+=self.length
        return True 

#--- ROL : Rotate left trough Carry
class opcode_ROL(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "ACC":
                val = cpu.getRegister(self.reg)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
                val = cpu.fetchMemory(addr)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr)
        c = cpu.getFlagC()
        ret = (val << 1) | c
        cpu.setFlagNZ(ret)
        cpu.setFlagC(val<<1) # move bit 7 into C flag
        cpu.SR = cpu.SR | 0x02 if ((cpu.SR ^ (cpu.SR>>3) ) & 0x01) else cpu.SR & 0xFD # set flag V as xor between new N and new C
        match self.type:
            case "ACC":
                cpu.setRegister(self.reg,ret % 256)
            case "IDX":
                cpu.setMemory(addr,ret & 0xFF)
            case "EXT":
                cpu.setMemory(addr,ret & 0xFF)
        cpu.PC+=self.length
        return True

#--- ROR : Rotate Right trough Carry
class opcode_ROR(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "ACC":
                val = cpu.getRegister(self.reg)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)+cpu.IX
                val = cpu.fetchMemory(addr)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr)
        c = cpu.getFlagC()
        ret = (val >> 1) | (c<<7)
        cpu.setFlagNZ(ret)
        cpu.setFlagC(val & 0x01) # move bit 0 into C flag
        cpu.SR = cpu.SR | 0x02 if ((cpu.SR ^ (cpu.SR>>3) ) & 0x01) else cpu.SR & 0xFD # set flag V as xor between new N and new C
        match self.type:
            case "ACC":
                cpu.setRegister(self.reg,ret % 256)
            case "IDX":
                cpu.setMemory(addr,ret & 0xFF)
            case "EXT":
                cpu.setMemory(addr,ret & 0xFF)
        cpu.PC+=self.length
        return True


#--- RTI : Return from Interrupt
class opcode_RTI(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        cpu.SR = cpu.fetchMemory(cpu.SP+1) #[SR] ← [[SP] + 1],
        cpu.B = cpu.fetchMemory(cpu.SP+2)  #[B] ← [[SP] + 2],
        cpu.A = cpu.fetchMemory(cpu.SP+3)  #[A] ← [[SP] + 3],
        cpu.IX = cpu.fetchMemory(cpu.SP+4)*256+cpu.fetchMemory(cpu.SP+5) #[X(HI)] ← [[SP] + 4],[X(LO)] ← [[SP] + 5],
        cpu.PC = cpu.fetchMemory(cpu.SP+6)*256+cpu.fetchMemory(cpu.SP+7) #[PC(HI)] ← [[SP] + 6],[PC(LO)] ← [[SP] + 7],
        cpu.SP+=7 #[SP] ← [SP] + 7
        return True

#--- RTS : Return from Subroutine
class opcode_RTS(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        cpu.PC = cpu.fetchMemory(cpu.SP+1)*256+cpu.fetchMemory(cpu.SP+2) #[PC(HI)] ← [[SP] + 1],[PC(LO)] ← [[SP] + 2],
        cpu.SP+=2 #[SP] ← [SP] + 2
        return True


#--- SBA : Subtract Accumulators
class opcode_SBA(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
        
    def execute(self,cpu):
        R = (cpu.A-cpu.B)
        cpu.setFlagNZVC(cpu.A,cpu.B,R)
        cpu.A = R & 0xFF
        cpu.PC+=1
        return True
 

#--- SBC : Subtract Mem and Carry Flag from Accumulator
class opcode_SBC(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)

    def execute(self,cpu):
        match self.type:
            case "IMM":
                val = cpu.fetchMemory(cpu.PC+1)
            case "DIR":
                addr8 = cpu.fetchMemory(cpu.PC+1)
                val = cpu.fetchMemory(addr8)
            case "IDX":
                addr8 = cpu.fetchMemory(cpu.PC+1)
                val = cpu.fetchMemory(addr8+cpu.IX)
            case "EXT":
                addr16 = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr16)
        c = cpu.getFlagC()
        r = cpu.getRegister(self.reg)
        ret = r - val - c
        cpu.setFlagNZVC(r,val,ret)
        cpu.setRegister(self.reg, ret & 0xFF)
        cpu.PC+=self.length
        return True


#--- SEC : Set the Carry Flag
class opcode_SEC(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
        
    def execute(self,cpu):
        cpu.SR = cpu.SR | 0x01 # carry Flag
        cpu.PC+=1
        return True


#--- SEI : Set the Interrupt Flag to disable interrupts
class opcode_SEI(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        cpu.setFlagI(1)
        cpu.PC+=1
        return True


#--- SEV : Set Overflow Flag
class opcode_SEV(opcode):
    def __init__(self, code, length, text, type, reg):
        super().__init__(code, length, text, type, reg)
    
    def execute(self,cpu):
        cpu.SR = cpu.SR | 0x02
        cpu.PC+=1
        return


#--- STA : Store Accumulator in memory
class opcode_STA(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)

    def execute(self,cpu):
        val = cpu.getRegister(self.reg)
        match self.type:
            case "DIR":
                addr8 = cpu.fetchMemory(cpu.PC+1)
                cpu.setMemory(addr8,val)
            case "IDX":
                addr8 = cpu.fetchMemory(cpu.PC+1)
                cpu.setMemory(addr8+cpu.IX, val)
            case "EXT":
                addr16 = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                cpu.setMemory(addr16,val)
        cpu.setFlagNZ(val)
        cpu.resetFlagV()
        cpu.PC+=self.length
        return True


class opcode_STS(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)

    def execute(self,cpu):
        val = cpu.SP
        match self.type:
            case "DIR":
                addr8 = cpu.fetchMemory(cpu.PC+1)
                cpu.setMemory(addr8,val>>8)
                cpu.setMemory(addr8+1,val & 0xFF)
            case "IDX":
                addr8 = cpu.fetchMemory(cpu.PC+1)
                cpu.setMemory(addr8+cpu.IX, val>>8)
                cpu.setMemory(addr8+cpu.IX_1, val & 0xFF)
            case "EXT":
                addr16 = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                cpu.setMemory(addr16,val>>8)
                cpu.setMemory(addr16+1,val & 0xFF)
        cpu.setFlagNZ(val)
        cpu.resetFlagV()
        cpu.PC+=self.length
        return True


class opcode_STX(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)

    def execute(self,cpu):
        val = cpu.IX
        match self.type:
            case "DIR":
                addr8 = cpu.fetchMemory(cpu.PC+1)
                cpu.setMemory(addr8,val>>8)
                cpu.setMemory(addr8+1,val & 0xFF)
            case "IDX":
                addr8 = cpu.fetchMemory(cpu.PC+1)
                cpu.setMemory(addr8+cpu.IX, val>>8)
                cpu.setMemory(addr8+cpu.IX_1, val & 0xFF)
            case "EXT":
                addr16 = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                cpu.setMemory(addr16,val>>8)
                cpu.setMemory(addr16+1,val & 0xFF)
        cpu.setFlagNZ(val)
        cpu.resetFlagV()
        cpu.PC+=self.length
        return True


#--- SUB : Subtract Memory contents from Accumulator
class opcode_SUB(opcode):    
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "IMM":
                val = cpu.fetchMemory(cpu.PC+1)
            case "DIR":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1))
            case "IDX":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1)+cpu.IX)
            case "EXT":
                val = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2))
        
        r = cpu.getRegister(self.reg)
        ret = r - val
        cpu.setFlagNZVC(r,val,ret)
        cpu.setRegister(self.reg,ret % 256)
        cpu.PC+=self.length
        return True


#--- SWI : Software Interrupt: push registers onto Stack, decrement Stack Pointer, and jump to interrupt subroutine.
class opcode_SWI(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        cpu.setMemory(cpu.SP,   cpu.PC & 0xFF)
        cpu.setMemory(cpu.SP-1, cpu.PC>>8)
        cpu.setMemory(cpu.SP-2, cpu.IX & 0xFF)
        cpu.setMemory(cpu.SP-3, cpu.IX>>8)
        cpu.setMemory(cpu.SP-4, cpu.A)
        cpu.setMemory(cpu.SP-5, cpu.B)
        cpu.setMemory(cpu.SP-6, cpu.SR)
        cpu.SP-=7
        cpu.PC = cpu.fetchMemory(0xFFFA)*256+cpu.fetchMemory(0xFFFB)
        cpu.setFlagI(1)
        return True


#--- TAB : Transfer A to B
class opcode_TAB(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        cpu.B = cpu.A
        cpu.resetFlagV()
        cpu.setFlagNZ(cpu.A)
        cpu.PC+=self.length
        return True


#--- TAP : Transfer A to Status Register
class opcode_TAP(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        cpu.SR = cpu.A | 0xC0
        cpu.PC+=self.length
        return True


#--- TBA : Transfer B to A
class opcode_TBA(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        cpu.A = cpu.B
        cpu.resetFlagV()
        cpu.setFlagNZ(cpu.A)
        cpu.PC+=self.length
        return True



#--- TPA : Transfer Status Register to A
class opcode_TPA(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        cpu.A = cpu.SR
        cpu.PC+=self.length
        return True
    

#--- TST : Test the accumulator
class opcode_TST(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        match self.type:
            case "ACC":
                val = cpu.getRegister(self.reg)
            case "IDX":
                addr = cpu.fetchMemory(cpu.PC+1)
                val = cpu.fetchMemory(addr+cpu.IX)
            case "EXT":
                addr = cpu.fetchMemory(cpu.PC+1)*256+cpu.fetchMemory(cpu.PC+2)
                val = cpu.fetchMemory(addr)
        cpu.setFlagNZ(val)
        cpu.resetFlagV()
        cpu.resetFlagC()
        cpu.PC+=self.length
        return True

    def decode(self,cpu,address):
        if self.type=="IDX":
            addr = cpu.fetchMemory(address+1)
            return f"{self.text} [IX+{addr:02X}] [{(addr+cpu.IX):04X}] ({(cpu.fetchMemory(addr+cpu.IX)):02X})" 
        return super(opcode_TST,self).decode(cpu,address)        

#--- TSX : Move Stack Pointer contents to Index register and increment.
class opcode_TSX(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        cpu.IX = (cpu.SP+1) & 0xFFFF
        cpu.PC+=self.length
        return True


#--- TXS : Move Index register contents to Stack Pointer and decrement.
class opcode_TXS(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu):
        cpu.SP = (cpu.IX-1) & 0xFFFF
        cpu.PC+=self.length
        return True
    

#--- WAI : Wait for Interrupt
class opcode_WAI(opcode):
    def __init__(self,opcode,length,text,type,reg):
        super().__init__(opcode,length,text,type,reg)
    
    def execute(self,cpu, stage=0):
        if stage==0:
            #cpu.CPU+=1
            cpu.setMemory(cpu.SP,   (cpu.PC+1) & 0xFF)
            cpu.setMemory(cpu.SP-1, (cpu.PC+1) >>8)
            cpu.setMemory(cpu.SP-2, cpu.IX & 0xFF)
            cpu.setMemory(cpu.SP-3, cpu.IX>>8)
            cpu.setMemory(cpu.SP-4, cpu.A)
            cpu.setMemory(cpu.SP-5, cpu.B)
            cpu.setMemory(cpu.SP-6, cpu.SR)
            cpu.SP-=7
            # the CPU really waits in here
            return False #for now we stop the debugger
        else:
            #we received an interrupt: in debugger simulated with the command INT
            cpu.PC = cpu.fetchMemory(0xFFFF-7)*256+cpu.fetchMemory(0xFFFF-6)
            cpu.setFlagI(1)
        return True


opcodes = [
    opcode_ABA(0x1B,1,"ABA","ACC",""),

    opcode_ADC(0x89,2,"ADC","IMM","A"),
    opcode_ADC(0x99,2,"ADC","DIR","A"),
    opcode_ADC(0xA9,2,"ADC","IDX","A"),
    opcode_ADC(0xB9,3,"ADC","EXT","A"),
    opcode_ADC(0xC9,2,"ADC","IMM","B"),
    opcode_ADC(0xD9,2,"ADC","DIR","B"),
    opcode_ADC(0xE9,2,"ADC","IDX","B"),
    opcode_ADC(0xF9,3,"ADC","EXT","B"),
    
    opcode_ADD(0x8B,2,"ADD","IMM","A"),
    opcode_ADD(0x9B,2,"ADD","DIR","A"),
    opcode_ADD(0xAB,2,"ADD","IDX","A"),
    opcode_ADD(0xBB,3,"ADD","EXT","A"),
    opcode_ADD(0xCB,2,"ADD","IMM","B"),
    opcode_ADD(0xDB,2,"ADD","DIR","B"),
    opcode_ADD(0xEB,2,"ADD","IDX","B"),
    opcode_ADD(0xFB,3,"ADD","EXT","B"),

    opcode_AND(0x84,2,"AND","IMM","A"),
    opcode_AND(0x94,2,"AND","DIR","A"),
    opcode_AND(0xA4,2,"AND","IDX","A"),
    opcode_AND(0xB4,3,"AND","EXT","A"),
    opcode_AND(0xC4,2,"AND","IMM","B"),
    opcode_AND(0xD4,2,"AND","DIR","B"),
    opcode_AND(0xE4,2,"AND","IDX","B"),
    opcode_AND(0xF4,3,"AND","EXT","B"),

    opcode_ASL(0x48,1,"ASL","ACC","A"),
    opcode_ASL(0x58,1,"ASL","ACC","B"),
    opcode_ASL(0x68,2,"ASL","IDX",""),
    opcode_ASL(0x78,3,"ASL","EXT",""),

    opcode_ASR(0x47,1,"ASR","ACC","A"),
    opcode_ASR(0x57,1,"ASR","ACC","B"),
    opcode_ASR(0x67,2,"ASR","IDX",""),
    opcode_ASR(0x77,3,"ASR","EXT",""),
    
    opcode_BCC(0x24,2,"BCC", "REL",""),
    opcode_BCS(0x25,2,"BCS", "REL",""),
    opcode_BEQ(0x27,2,"BEQ", "REL",""),
    opcode_BGE(0x2C,2,"BGE", "REL",""),
    opcode_BGT(0x2E,2,"BGT", "REL",""),
    opcode_BHI(0x22,2,"BHI", "REL",""),

    opcode_BIT(0x85,2,"BIT","IMM","A"),
    opcode_BIT(0x95,2,"BIT","DIR","A"),
    opcode_BIT(0xA5,2,"BIT","IDX","A"),
    opcode_BIT(0xB5,3,"BIT","EXT","A"),
    opcode_BIT(0xC5,2,"BIT","IMM","B"),
    opcode_BIT(0xD5,2,"BIT","DIR","B"),
    opcode_BIT(0xE5,2,"BIT","IDX","B"),
    opcode_BIT(0xF5,3,"BIT","EXT","B"),

    opcode_BLE(0x2F,2,"BLE", "REL", ""),
    opcode_BLS(0x23,2,"BLS", "REL", ""),
    opcode_BLT(0x2D,2,"BLT", "REL", ""),
    opcode_BMI(0x2B,2,"BMI", "REL", ""),
    opcode_BNE(0x26,2,"BNE", "REL", ""),
    opcode_BPL(0x2A,2,"BPL", "REL", ""),
    opcode_BRA(0x20,2,"BRA", "REL", ""),
    opcode_BSR(0x8D,2,"BSR", "REL", ""),
    opcode_BVC(0x28,2,"BVC", "REL", ""),
    opcode_BVS(0x29,2,"BVS", "REL", ""),

    opcode_CBA(0x11,1,"CBA", "INH", ""),
    opcode_CLC(0x0C,1,"CLC", "INH", ""),
    opcode_CLI(0x0E,1,"CLI", "INH", ""),
    opcode_DAA(0x19,1,"DAA", "INH", "A"),

    opcode_CLR(0x4F,1,"CLR","ACC","A"),
    opcode_CLR(0x5F,1,"CLR","ACC","B"),
    opcode_CLR(0x6F,2,"CLR","IDX",""),
    opcode_CLR(0x7F,3,"CLR","EXT",""),

    opcode_CLV(0x0A,1,"CLV","INH", ""),
    opcode_CMP(0x81,2,"CMP","IMM","A"),
    opcode_CMP(0x91,2,"CMP","DIR","A"),
    opcode_CMP(0xA1,2,"CMP","IDX","A"),
    opcode_CMP(0xB1,3,"CMP","EXT","A"),
    opcode_CMP(0xC1,2,"CMP","IMM","B"),
    opcode_CMP(0xD1,2,"CMP","DIR","B"),
    opcode_CMP(0xE1,2,"CMP","IDX","B"),
    opcode_CMP(0xF1,3,"CMP","EXT","B"),

    opcode_COM(0x43,1,"COM","ACC","A"),
    opcode_COM(0x53,1,"COM","ACC","B"),
    opcode_COM(0x63,2,"COM","IDX",""),
    opcode_COM(0x73,3,"COM","EXT",""),

    opcode_CPX(0x9C,2,"CPX","DIR","IX"),
    opcode_CPX(0xAC,2,"CPX","IDX","IX"),
    opcode_CPX(0x8C,3,"CPX","IMM","IX"),
    opcode_CPX(0xBC,3,"CPX","EXT","IX"),

    opcode_DAA(0x19,1,"DAA", "INH","A"),

    opcode_DEC(0x4A,1,"DEC","ACC","A"),
    opcode_DEC(0x5A,1,"DEC","ACC","B"),
    opcode_DEC(0x6A,2,"DEC","IDX","IX"),
    opcode_DEC(0x7A,3,"DEC","EXT",""),

    opcode_DES(0x34,1,"DES", "INH", ""),
    opcode_DEX(0x09,1,"DEX", "INH", ""),

    opcode_EOR(0x88,2,"EOR","IMM","A"),
    opcode_EOR(0x98,2,"EOR","DIR","A"),
    opcode_EOR(0xA8,2,"EOR","IDX","A"),
    opcode_EOR(0xB8,3,"EOR","EXT","A"),
    opcode_EOR(0xC8,2,"EOR","IMM","B"),
    opcode_EOR(0xD8,2,"EOR","DIR","B"),
    opcode_EOR(0xE8,2,"EOR","IDX","B"),
    opcode_EOR(0xF8,3,"EOR","EXT","B"),

    opcode_INC(0x4C,1,"INC","ACC","A"),
    opcode_INC(0x5C,1,"INC","ACC","B"),
    opcode_INC(0x6C,2,"INC","IDX","IX"),
    opcode_INC(0x7C,3,"INC","EXT",""),

    opcode_INS(0x31,1,"INS", "INH", ""),
    opcode_INX(0x08,1,"INX", "INH", ""),

    opcode_JMP(0x6E,2,"JMP", "IDX", "IX"),
    opcode_JMP(0x7E,3,"JMP", "EXT", "PC"),

    opcode_JSR(0xAD,2,"JSR", "IDX", "IX"),
    opcode_JSR(0xBD,3,"JSR", "EXT", ""),

    opcode_LDA(0x86,2,"LDA","IMM","A"),
    opcode_LDA(0x96,2,"LDA","DIR","A"),
    opcode_LDA(0xA6,2,"LDA","IDX","A"),
    opcode_LDA(0xB6,3,"LDA","EXT","A"),
    opcode_LDA(0xC6,2,"LDA","IMM","B"),
    opcode_LDA(0xD6,2,"LDA","DIR","B"),
    opcode_LDA(0xE6,2,"LDA","IDX","B"),
    opcode_LDA(0xF6,3,"LDA","EXT","B"),

    opcode_LDS(0x9E,2,"LDS","DIR","SP"),
    opcode_LDS(0xAE,2,"LDS","IDX","SP"),
    opcode_LDS(0x8E,3,"LDS","IMM","SP"),
    opcode_LDS(0xBE,3,"LDS","EXT","SP"),

    opcode_LDX(0xDE,2,"LDX","DIR","IX"),
    opcode_LDX(0xEE,2,"LDX","IDX","IX"),
    opcode_LDX(0xCE,3,"LDX","IMM","IX"),
    opcode_LDX(0xFE,3,"LDX","EXT","IX"),

    opcode_LSR(0x44,1,"LSR","ACC","A"),
    opcode_LSR(0x54,1,"LSR","ACC","B"),
    opcode_LSR(0x64,2,"LSR","IDX","IX"),
    opcode_LSR(0x74,3,"LSR","EXT",""),

    opcode_NEG(0x40,1,"NEG","ACC","A"),
    opcode_NEG(0x50,1,"NEG","ACC","B"),
    opcode_NEG(0x60,2,"NEG","IDX","IX"),
    opcode_NEG(0x70,3,"NEG","EXT",""),

    opcode_NOP(0x01,1,"NOP","INH",""),

    opcode_ORA(0x8A,2,"ORA","IMM","A"),
    opcode_ORA(0x9A,2,"ORA","DIR","A"),
    opcode_ORA(0xAA,2,"ORA","IDX","A"),
    opcode_ORA(0xBA,3,"ORA","EXT","A"),
    opcode_ORA(0xCA,2,"ORA","IMM","B"),
    opcode_ORA(0xDA,2,"ORA","DIR","B"),
    opcode_ORA(0xEA,2,"ORA","IDX","B"),
    opcode_ORA(0xFA,3,"ORA","EXT","B"),

    opcode_PSH(0x36,1,"PSH","ACC","A"),
    opcode_PSH(0x37,1,"PSH","ACC","B"),
    opcode_PUL(0x32,1,"PUL","ACC","A"),
    opcode_PUL(0x33,1,"PUL","ACC","B"),

    opcode_ROL(0x49,1,"ROL","ACC","A"),
    opcode_ROL(0x59,1,"ROL","ACC","B"),
    opcode_ROL(0x69,2,"ROL","IDX","IX"),
    opcode_ROL(0x79,3,"ROL","EXT",""),

    opcode_ROR(0x46,1,"ROR","ACC","A"),
    opcode_ROR(0x56,1,"ROR","ACC","B"),
    opcode_ROR(0x66,2,"ROR","IDX","IX"),
    opcode_ROR(0x76,3,"ROR","EXT",""),

    opcode_RTI(0x3B,1,"RTI",  "INH",""),
    opcode_RTS(0x39,1,"RTS",  "INH",""),

    opcode_SBA(0x10,1,"SBA",  "INH",""),

    opcode_SBC(0x82,2,"SBC","IMM","A"),
    opcode_SBC(0x92,2,"SBC","DIR","A"),
    opcode_SBC(0xA2,2,"SBC","IDX","A"),
    opcode_SBC(0xB2,3,"SBC","EXT","A"),
    opcode_SBC(0xC2,2,"SBC","IMM","B"),
    opcode_SBC(0xD2,2,"SBC","DIR","B"),
    opcode_SBC(0xE2,2,"SBC","IDX","B"),
    opcode_SBC(0xF2,3,"SBC","EXT","B"),

    opcode_SEC(0x0D,1,"SEC",  "INH",""),

    opcode_SEI(0x0F,1,"SEI",  "INH",""),

    opcode_SEV(0x0B,1,"SEV",  "INH",""),

    opcode_STA(0x97,2,"STA","DIR","A"),
    opcode_STA(0xA7,2,"STA","IDX","A"),
    opcode_STA(0xB7,3,"STA","EXT","A"),
    opcode_STA(0xD7,2,"STA","DIR","B"),
    opcode_STA(0xE7,2,"STA","IDX","B"),
    opcode_STA(0xF7,3,"STA","EXT","B"),

    opcode_STS(0x9F,2,"STS","DIR","SP"),
    opcode_STS(0xAF,2,"STS","IDX","SP"),
    opcode_STS(0xBF,3,"STS","EXT","SP"),
    
    opcode_STX(0xDF,2,"STX","DIR","IX"),
    opcode_STX(0xEF,2,"STX","IDX","IX"),
    opcode_STX(0xFF,3,"STX","EXT","IX"),

    opcode_SUB(0x80,2,"SUB","IMM","A"),
    opcode_SUB(0x90,2,"SUB","DIR","A"),
    opcode_SUB(0xA0,2,"SUB","IDX","A"),
    opcode_SUB(0xB0,3,"SUB","EXT","A"),
    opcode_SUB(0xC0,2,"SUB","IMM","B"),
    opcode_SUB(0xD0,2,"SUB","DIR","B"),
    opcode_SUB(0xE0,2,"SUB","IDX","B"),
    opcode_SUB(0xF0,3,"SUB","EXT","B"),

    opcode_SWI(0x3F,1,"SWI",  "INH",""),

    opcode_TAB(0x16,1,"TAB", "INH","A->B"),
    opcode_TAP(0x06,1,"TAP", "INH","A->SR"),
    opcode_TBA(0x17,1,"TBA", "INH","B->A"),
    opcode_TPA(0x07,1,"TPA", "INH","SR->A"),

    opcode_TST(0x4D,1,"TST","ACC","A"),
    opcode_TST(0x5D,1,"TST","ACC","B"),
    opcode_TST(0x6D,2,"TST","IDX","IX"),
    opcode_TST(0x7D,3,"TST","EXT",""),

    opcode_TSX(0x30,1,"TSX",  "INH",""),
    opcode_TXS(0x35,1,"TXS",  "INH",""),

    opcode_WAI(0x3E,1,"WAI",  "INH",""),

]



if __name__ == '__main__':

    def fetchMem(addr):
        return 0
    
    cpu = MC6800(fetchMem,fetchMem)

    for op in opcodes:
        print(f"{op.code:02X} {op.length} {op.text:3s} {op.type:3s} {op.reg:2s} | {op.decode(cpu,0)}")