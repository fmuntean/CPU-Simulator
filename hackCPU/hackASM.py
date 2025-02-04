"""
 hack CPU assembler
"""


from sys import argv

from utils.hackAssembler import HackAssembler


def help():
  print()
  print("Hack Assembler:")
  print("usage: ./hackASM <asmFile>")
  print()
  pass

if __name__ == '__main__':
  if len(argv)==1:
    help()
  else:  
    asmFile = argv[1]
    #asmFile = "hackCPU/pong/pong.asm" # argv[1]
    #asmFile = "hackCPU/Lab06/Rect.asm"
    #asmFile = "hackCPU/hackCPU.asm"
    romFile = asmFile[:-3]+'rom' # replace .asm with .rom
    lstFile = asmFile[:-3]+'lst' # replace .asm with .lst
    with open(asmFile,mode="r") as asm:
      HackAssembler.pass1(asm)

    with open(asmFile,mode="r") as asm:
      with open(romFile,mode="w") as rom:
        with open(lstFile,mode="w") as lst:
          HackAssembler.assemble(asm,rom,lst)
          HackAssembler.listVars(lst)
          HackAssembler.listLabels(lst)