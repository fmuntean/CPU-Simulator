#!/usr/bin/python

# simple compiler for myCPU

import sys,getopt
from myCpu import opcodes

inFile = "sample.asm"
outFile = "sample.hex"


try:
    args, values = getopt.getopt(sys.argv[1:],"hi:o:",["ifile=","ofile="])
except getopt.GetoptError:
    print("compile.py -i <inputfile> -o <outputfile>")
    sys.exit(2)
print(str(values))
print(str(args))
for opt, arg in args:
    if opt == '-h':
        print("compile.py -i <inputfile> -o <outputfile>")
        sys.exit()
    elif opt in ("-i", "--ifile"):
        inFile = arg
    elif opt in ("-o", "--ofile"):
        outFile = arg
print('Input file is "', inFile)
print('Output file is "', outFile)



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

class Org(Number):
    def getHex(self):
        return f"\n{super().getHex():02X}: "
    pass

class Data:
    def __init__(self,data):
        self.data = data
    def getHex(self):
        return self.data

class Label:
    labels = {}
    def addLabel(label, num):
        Label.labels[label] = num.getHex()

    def __init__(self,label):
        self.label = label
    
    def getHex(self):
        return f"{Label.labels[self.label]:02X}"


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
        cnt = len(line.replace(","," ").strip().split(" "))
        #line = line.replace(".DATA", f"{Address.address:2X}:")
        lines.append(Data(line.replace(".DATA ","")))
        Address.add(cnt-1)
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

hex=""
for l in lines:
    hex+=" "+l.getHex()

print(hex)

with open(outFile,mode="w+") as f:
    f.write(hex)

