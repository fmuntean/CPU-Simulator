"""
:10246200464C5549442050524F46494C4500464C33
|||||||||||                              CC->Checksum
|||||||||DD->Data
|||||||TT->Record Type
|||AAAA->Address
|LL->Record Length
:->Colon
"""
def loadHex(mem,file):
    lines = []
    with open(file,mode="r") as f:
        lines = f.readlines()
    for l in lines:
        if len(l.strip())==0:
            continue
        if l.startswith('//'):
            continue
        if l.startswith(':') & (l[7:9] == '00'):
            count = int(l[1:3],base=16)
            addr = int(l[3:7],base=16)
            for i in range(0,count):
                d = l[9+2*i:9+2*i+2]
                mem[addr]= int(d,base=16)
                addr+=1

def saveHex(mem,file,start,size,lineSize=32):
    lines=[]

    addr=start
    while ( addr < start+size ):
        l = (addr+lineSize) % lineSize if ( (addr+lineSize) > (start+size) ) else lineSize

        
        checksum = (l+(addr>>8)+(addr&0xFF)) & 0xFF

        line = f":{l:02X}{addr:04X}00"

        #write the data as hex
        for i in range(l):
            line+=f"{(mem[addr+i]):02X}"
            checksum+=mem[addr+i]

        
        checksum = ((checksum ^ 0xFF)+1)&0xFF

        line+=f"{checksum:02X}\n"
        lines+=line
        addr +=l #move to next address block

    #write the final line
    lines+=':00000001FF'
    with open(file,mode="w") as f:
        f.writelines(lines)
    
    


# https://en.wikipedia.org/wiki/SREC_(file_format)
# loading motorola s19 files
# currently supporting S1 records
def loadS19(mem,file):
    lines = []
    with open(file,mode="r") as f:
        lines = f.readlines()
    for l in lines:
        if len(l.strip())==0:
            continue
        if l.startswith('//'):
            continue
        if l.startswith('S1'):
            count = int(l[2:4],base=16)
            addr = int(l[4:8],base=16)
            for i in range(0,count-3):
                d = l[8+2*i:8+2*i+2]
                mem[addr]= int(d,base=16)
                addr+=1


if __name__ == '__main__':
    mem = bytearray(0x10000) 
    loadHex(mem,'D:/git/arduino/ePromProgrammer/ROMS/EPROM_2K_TMS2516.hex')
    #loadHex(mem,'swtb2.hex')
    saveHex(mem,'test.hex',0x00,2048,32)