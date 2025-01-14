"""
VMTranslator
• Constructs a Parser to handle the input file;
• Constructs a CodeWriter to handle the output file;
• Iterates through the input file, parsing each line and generating
assembly code from it, using the services of the Parser and a CodeWriter.
"""



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
          if line.startswith('//'):
            self.writer.WriteComment(line)
            continue
          
          self.writer.WriteComment(f"//{line}")
          
          cmd,arg1,arg2 = self.parser.Parse(line)
          self.writer.Translate(cmd,arg1,arg2)

      


if __name__ == '__main__':
  vmFile = "BasicTest.vm" #argv[0]
  asmFile = vmFile[:-3]+".asm"
  with open(asmFile,mode="w") as asm:
    with open(vmFile,mode="r") as f:
      writer = CodeWriter(asm)
      parser = Parser()
      translator = VMTranslator(parser,writer)
      translator.Translate(f)
    