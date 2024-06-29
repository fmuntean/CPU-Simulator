#!/usr/bin/python

# simple compiler for myCPU

import sys,getopt
from sampleCpu import opcodes
    

class Address:
    address = 0
    def setAddress(addr):
        Address.address = addr
    def inc():
        Address.address+=1
    def add(num):
        Address.address+=num
    
class Number:
    def __init__(self,num):
        self.num = num
    def getHex(self):
        return self.num
    def getVal(self):
        return self.num

class Org(Number):
    def getVal(self):
        return super().getVal()
    def getHex(self):
        return f"\n{super().getHex():02X}: "
    pass

class Data:
    def __init__(self,data):
        self.data = data
    def getHex(self):
        return self.data
    def getVal(self):
        return int(self.data,base=16)

class Label:
    labels = {}
    def addLabel(label, num):
        Label.labels[label] = num.getHex()

    def __init__(self,label):
        self.label = label
    
    def getHex(self):
        return f"{Label.labels[self.label]:02X}"
    def getVal(self):
        return Label.labels[self.label]


def parseLine(line):
    ret =[]
    token=""
    for c in line:
        if c in [',',':',' ']:
            if len(token)>0:
                ret.append(token)
            token=":" if c==':' else ""
        else:
            token+=c
    ret.append(token.strip())
    return ret

def compile(inFile, outFile):
    #read the asm file into memory and remove any comments
    asm = []
    with open(inFile) as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            i = line.find(';')
            if i==0:
                continue
            if i>0:
                line = line[0:i-1]
            if len(line)==0:
                continue

            asm.append(line.upper())


    #parse the asm and generate hex
    lines = []
    for line in asm:
        if line[0]==':':
            Label.addLabel(line, Number(Address.address))
            continue
        if line.startswith(".ORG"):
            Address.setAddress(int(line[5:len(line)],base=16))
            lines.append(Org(Address.address))
            continue
        if line.startswith(".DATA"):
            vals = line.replace(".DATA ","").replace(","," ").strip().split(" ")
            cnt = len(vals)
            #line = line.replace(".DATA", f"{Address.address:2X}:")
            for v in vals:
                lines.append(Data(v))
            Address.add(cnt)
            continue
        #now we can parse the opcodes
        tokens = parseLine(line)
        #first one is the operation
        ops = list(filter(lambda x: x.text == tokens[0], opcodes))
        if len(ops) == 0:
            ops = list(filter(lambda x: x.text.startswith(tokens[0]), opcodes))
            if len(ops)>1:
                newToken  = f"{tokens[0]} {tokens.pop(1)}"
                tokens[0] = newToken
                ops = list(filter(lambda x: x.text == tokens[0], ops))
        if len(ops)==0:
            raise Exception(f"invalid opcode: {line}")
        
        op = ops[0]
        lines.append(op)
        Address.inc()
        for i in range(1,op.length):
            token = tokens[i]
            Address.inc()
            if token.startswith(":"):
                lines.append(Label(token))
            else:
                lines.append(Number(token))

    """
    :10246200464C5549442050524F46494C4500464C33
    |||||||||||                              CC->Checksum
    |||||||||DD->Data
    |||||||TT->Record Type
    |||AAAA->Address
    |LL->Record Length
    :->Colon
    """
    hex=""
    addr = 0
    line = ""
    checksum=0
    recordLen = 0
    for l in lines:
        if type(l) is Org:
            addr = l.getVal()
            if recordLen>0:
                hex+=f"\n:{recordLen:02X}{line}{checksum:02X}"    
                recordLen = 0
                checksum = 0
            line=f"{addr:04X}00"
            checksum = (checksum + addr) & 0xFF
        elif recordLen % 16 == 0 and recordLen>0:
            #complete current line
            hex+=f"\n:{recordLen:02X}{line}{checksum:02X}"    
            recordLen = 0
            checksum = 0
        else:
            line+=l.getHex()
            addr+=1
            recordLen+=1
            checksum= (checksum + int(l.getHex(),base=16)) & 0xFF
        

    print(hex)

    with open(outFile,mode="w+") as f:
        f.write(hex)



if __name__ == '__main__':
    inFile = "sampleCPU/sample.asm"
    outFile = None
    try:
        args, values = getopt.getopt(sys.argv[1:],"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print("compile.py -i <inputfile> -o <outputfile>")
        sys.exit(2)
    #print(str(values))
    #print(str(args))
    for opt, arg in args:
        if opt == '-h':
            print("compile.py -i <inputfile> -o <outputfile>")
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inFile = arg
        elif opt in ("-o", "--ofile"):
            outFile = arg
    if inFile == None:
        print("compile.py -i <inputfile> -o <outputfile>")
        sys.exit(2)
    if outFile == None:
        outFile = inFile.split('.')[0]+".hex"
    print('Input file is "', inFile)
    print('Output file is "', outFile)
    compile(inFile,outFile)