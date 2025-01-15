"""
VMTranslator
• Constructs a Parser to handle the input file;
• Constructs a CodeWriter to handle the output file;
• Iterates through the input file, parsing each line and generating
assembly code from it, using the services of the Parser and a CodeWriter.
"""



import os
import string
from sys import argv

from CodeWriter import CodeWriter
from Parser import  Parser



class VMTranslator:
  def __init__(self,parser:Parser,writer:CodeWriter):
    self.parser = parser
    self.writer = writer
    pass

  def Translate(self,f):
        for line in f:
          if len(line)==0:
            continue
          if line =='\n':
            continue
          if line.strip().startswith('//'):
            self.writer.WriteComment(line)
            continue
          
          self.writer.WriteComment(f"\n//{line}")
          
          cmd,arg1,arg2 = self.parser.Parse(line)
          arg2 = 0 if arg2 in (None,'','//')  else int(arg2)
          self.writer.Translate(cmd,arg1,arg2)


def getVMFiles(folder:string):
  ret =[]
   # r=root, d=directories, f = files
  for r, d, f in os.walk(vmFolder):
    for file in f:
      if file.endswith(".vm"):
          ret.append(os.path.join(r, file))
  return ret



if __name__ == '__main__':
  vmFolder = 'lab08\\FibonacciElement' #argv[1]
  asmFile = vmFolder.split(os.path.sep)[-1]+".asm"
    
  with open(asmFile,mode="w") as asm:
    writer = CodeWriter(asm)
    writer.WriteBoostrap()
    parser = Parser()
    for vmFile in getVMFiles(vmFolder):
      with open(vmFile,mode="r") as f:
        _,sourceFile=os.path.split(vmFile)
        writer.source = sourceFile[:-3]
        writer.WriteComment(f"\n// Processing file: {vmFile}\n")
        translator = VMTranslator(parser,writer)
        translator.Translate(f)

    