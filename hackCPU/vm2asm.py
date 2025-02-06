"""
VMTranslator
• Constructs a Parser to handle the input file;
• Constructs a CodeWriter to handle the output file;
• Iterates through the input file, parsing each line and generating
assembly code from it, using the services of the Parser and a CodeWriter.
"""



import os
from sys import argv

from utils.CodeWriter import CodeWriter
from utils.Parser import Parser
from utils.utils import getVMFiles
from utils.vmTranslator import VMTranslator





def help():
  print()
  print("VM2ASM:")
  print("usage: ./vm2asm <pathToFolder> | <filename>")
  print()
  pass


def compileFile(vmFile,asm):
  with open(vmFile,mode="r") as f:
    _,sourceFile=os.path.split(vmFile)
    writer.source = sourceFile[:-3]
    writer.WriteComment(f"\n// Processing file: {vmFile}\n")
    
    translator.Translate(f)


if __name__ == '__main__':
  #vmFolder = 'lab08\\FibonacciElement' #argv[1]

  if len(argv)==1:
    help()
  else:
    

    vmFolder = argv[1]
    if vmFolder.endswith('.vm'): #we have a file
      asmFile = vmFolder.replace('.vm',".asm")
      print(f"Generating asm file: {asmFile}")
      with open(asmFile,mode="w") as asm:
        parser = Parser()
        writer = CodeWriter(asm)
        translator = VMTranslator(parser,writer,version=4)
        compileFile(vmFolder,asm)
    else: # we have a folder
      asmFile = vmFolder+'/'+vmFolder.replace('/','\\').split(os.path.sep)[-1]+".asm"
      print(f"Generating asm file: {asmFile}")
      with open(asmFile,mode="w") as asm:
        parser = Parser()
        writer = CodeWriter(asm)
        translator = VMTranslator(parser,writer,version=4)
    
        for srcFile in getVMFiles(vmFolder):
          print(f"Processing File: {srcFile}")
          compileFile(srcFile,asm)
    print("Done.")
    