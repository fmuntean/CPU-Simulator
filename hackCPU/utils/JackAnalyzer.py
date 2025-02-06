import string

from utils.CompilationEngine import CompilationEngine
from utils.JackTokenizer import JackTokenizer
from utils.VmWriter import VmWriter


class JackAnalyzer:

  def __init__(self,srcFile:string,vmFile):
    self.tknzr = JackTokenizer(srcFile)
    self.vm = VmWriter(vmFile)
    self.ce = CompilationEngine(self.tknzr,self.vm,version=2)
    self.srcFile = srcFile

  #Version 0: Designed to test the JackTokenizer
  def extractTokens(self):
    #self.ce.nextToken(); # gets the first token
    while self.tknzr.hasMoreTokens():
      token = self.tknzr.advance()
      if token is not None:
        print(token.toXml())
        


  def execute(self):
    #tokens = []
    #xmlFile = self.srcFile[:-4]+'xml'
    #with open(xmlFile,mode='w') as xml:
      token = self.tknzr.advance() # gets the first token 
      while (token.tokenType!='keyword'):
        #tokens.append(token)
        if token.tokenType == 'comment':
          self.vm.writeComment(token.val)
       #   xml.write(token.toXml())
       #   xml.write('\n')
          token = self.tknzr.advance()
        else:
          print (f"ERROR: invalid token")
          print(token.toXml())

      token = self.ce.compileClass()
      #tokens.append(token)
      #xml.write(token.toXml())
      return #tokens
  
#------------------------------------------------------------
