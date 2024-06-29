
class opcode:
    length= 0
    code = 0
    text = ""
    def __init__(self,code,length, text):
        self.code = code
        self.length = length 
        self.text = text

    def getHex(self):
        ret = f"{self.code:02X}"
        return ret

    def getText(self):
        return self.text

    def decode(self,cpu,address):
        ret = self.text
        if self.length>1: #it is a two byte instruction
            ret+=f",{cpu.fetchMemory(address+1):02X}"
        return ret
    
class opcode_NOP(opcode):    
    def __init__(self):
        self.code = 0
        self.length = 1
        self.text = "NOP"
    def execute(self,cpu):
        cpu.PC+=1
        return True 

class opcode_BREAK(opcode):
    def __init__(self):
        self.code=1
        self.length=1
        self.text = "BREAK"
    def execute(self,cpu):
        cpu.PC+=1
        return False #triggering the stop in debugger
    
class opcode_HALT(opcode):
    def __init__(self):
        self.code = 255
        self.length = 1
        self.text = "HALT"
    
    def execute(self,cpu):
        return False #trigerring the stop in debugger
   
class opcode_LC_A(opcode):
    def __init__(self):
        super().__init__(2,2,"LC A")

    def execute(self,cpu):
        cpu.registers[0] = cpu.fetchMemory(cpu.PC+1)
        cpu.ZERO = cpu.registers[0] == 0
        cpu.PC+=self.length
        return True
        
class opcode_LC_B(opcode):
    def __init__(self):
        super().__init__(3,2,"LC B")

    def execute(self,cpu):
        cpu.registers[1] = cpu.fetchMemory(cpu.PC+1)
        cpu.ZERO = cpu.registers[1] == 0
        cpu.PC+=self.length
        return True


class opcode_LD_A(opcode):
    def __init__(self):
        super().__init__(4,2,"LD A")

    def execute(self,cpu):
        cpu.registers[0] = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1))
        cpu.ZERO = cpu.registers[0] == 0
        cpu.PC+=self.length
        return True

class opcode_LD_B(opcode):
    def __init__(self):
        super().__init__(5,2,"LD B")

    def execute(self,cpu):
        cpu.registers[1] = cpu.fetchMemory(cpu.fetchMemory(cpu.PC+1))
        cpu.ZERO = cpu.registers[1] == 0
        cpu.PC+=self.length
        return True

class opcode_STOAB(opcode):
    def __init__(self):
        super().__init__(6,1,"STOAB")

    def execute(self,cpu):
        cpu.setMemory(cpu.registers[0],cpu.registers[1])
        cpu.PC+=self.length
        return True

class opcode_ST_A(opcode):
    def __init__(self):
        super().__init__(7,2,"ST A")

    def execute(self,cpu):
        cpu.setMemory(cpu.fetchMemory(cpu.PC+1), cpu.registers[0])
        cpu.PC+=self.length
        return True

class opcode_ST_B(opcode):
    def __init__(self):
        super().__init__(8,2,"ST B")

    def execute(self,cpu):
        cpu.setMemory(cpu.fetchMemory(cpu.PC+1), cpu.registers[1])
        cpu.PC+=self.length
        return True


class opcode_ADD(opcode):
    def __init__(self):
        super().__init__(9,1,"ADD")

    def execute(self,cpu):
        cpu.CARRY = cpu.registers[0]+cpu.registers[1] > 255
        cpu.registers[0] = (cpu.registers[0]+cpu.registers[1]) % 256
        cpu.ZERO = cpu.registers[0] == 0
        cpu.PC+=self.length
        return True

class opcode_SUB(opcode):
    def __init__(self):
        super().__init__(10,1,"SUB")

    def execute(self,cpu):
        
        cpu.CARRY = cpu.registers[0]-cpu.registers[1] < 0
        cpu.registers[0] = (cpu.registers[0]-cpu.registers[1]) % 256
        cpu.ZERO = cpu.registers[0] == 0
        cpu.PC+=self.length
        return True

class opcode_JMP(opcode):
    def __init__(self):
        super().__init__(11,2,"JMP")

    def execute(self,cpu):
        cpu.PC=cpu.fetchMemory(cpu.PC+1)
        return True

class opcode_JMPZ(opcode):
    def __init__(self):
        super().__init__(12,2,"JMPZ")

    def execute(self,cpu):
        cpu.PC= cpu.fetchMemory(cpu.PC+1) if cpu.ZERO else cpu.PC+self.length
        return True

class opcode_JMPC(opcode):
    def __init__(self):
        super().__init__(13,2,"JMPC")

    def execute(self,cpu):
        cpu.PC= cpu.fetchMemory(cpu.PC+1) if cpu.CARRY else cpu.PC+self.length
        return True


opcodes = [
    opcode_NOP(),
    opcode_BREAK(),
    opcode_HALT(),
    opcode_LC_A(),
    opcode_LC_B(),
    opcode_LD_A(),
    opcode_LD_B(),
    opcode_STOAB(),
    opcode_ST_A(),
    opcode_ST_B(),
    opcode_ADD(),
    opcode_SUB(),
    opcode_JMP(),
    opcode_JMPZ(),
    opcode_JMPC(),
    #to be implemented
    opcode(14,1,"AND"),
    opcode(15,1,"OR"),
    opcode(16,1,"LSR A"),
    opcode(17,1,"LSR B"),
    opcode(18,1,"LSL A"),
    opcode(19,1,"LSL B") 
]

class myCPU:
    
    def reset(self):
        self.PC = 0
        self.registers = [0,0]
        self.CARRY = False
        self.ZERO = True

    def __init__(self):
        self.reset()
        
    def step(self):
        op = list(filter(lambda x: x.code == self.fetchMemory(self.PC % 255), opcodes))[0]
        return op.execute(self)

    def getOpcode(self,index):
        op =  list(filter(lambda x: x.code == self.fetchMemory(index), opcodes))[0]
        return op
    
    def getRegistries(self):
        return "|PC:{0:04X}|A:{1:02X}|B:{2:02X}|Z:{3:d}|C:{4:d}|".format(self.PC, self.registers[0], self.registers[1], self.ZERO, self.CARRY )
    