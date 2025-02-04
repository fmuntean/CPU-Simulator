from utils import Parser
from utils.CodeWriter import CodeWriter


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

