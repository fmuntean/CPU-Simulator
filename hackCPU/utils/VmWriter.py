import string


class VmWriter:
  

  def __init__(self, outFile,logLevel=0, newOps=False):
    self.outFile = outFile
    self.logLevel=logLevel
    self.tab='    '
    self.newOperations = newOps; # specify if the VM implementation supports new operations 
    pass

  def writeComment(self,comment:string):
    if comment and self.logLevel>0:
      for msg in comment.split('\n'):
        self.outFile.write(f"// {msg}\n")

  def writeGoTo(self,lbl:string,comment=None):
    if comment and self.logLevel>0:
      self.outFile.write(f"\ngoto {lbl}{self.tab}// {comment}\n")
    else:
      self.outFile.write(f"{self.tab}goto {lbl}\n")

  def writeIfGoTo(self,lbl:string,comment=None):
    if comment and self.logLevel>0:
      self.outFile.write(f"\nif-goto {lbl}{self.tab}// {comment}\n")
    else:
      self.outFile.write(f"{self.tab}if-goto {lbl}\n")

  def writeCall(self,lbl:string, nArgs:int,comment=None):
    if comment and self.logLevel>0:
      self.outFile.write(f"call {lbl} {nArgs}{self.tab}// {comment}\n")
    else:
      self.outFile.write(f"{self.tab}call {lbl} {nArgs}\n")

  def writeLabel(self,lbl:string,comment=None):
    if comment and self.logLevel>0:
      self.outFile.write(f"label {lbl}{self.tab}// {comment}\n")
    else:
      self.outFile.write(f"label {lbl}\n")
  
  def writeArithmetic(self,op,comment=None):
    operations = {
      '+': 'add',
      '-': 'sub',
      '*': 'call Math.multiply 2', 
      '/': 'call Math.divide 2',
      '&': 'and',
      '|': 'or',
      '<': 'lt',
      '>': 'gt',
      '=': 'eq',
      '~': 'not',
      'neg':'neg'
    }

    newOperations = {
      '<=':'le',
      '>=':'ge'
    }
    
    if self.newOperations:
      operations +=newOperations
    else:
      #we need to handle the le and ge differently
      if op == '<=':
        self.outFile.write(f"{self.tab}gt\n{self.tab}not\n")
      if op == '>=':
        self.outFile.write(f"{self.tab}lt\n{self.tab}not\n")      
      


    if op in operations.keys():
      if comment and self.logLevel>0:
        self.outFile.write(f"{operations[op]}{self.tab}// {comment}\n")
      else:
        self.outFile.write(f"{self.tab}{operations[op]}\n")
    
    pass


  def writeReturn(self,comment=None):
    if comment and self.logLevel>0:
      self.outFile.write(f"return{self.tab}// {comment}\n")
    else:
      self.outFile.write(f"{self.tab}return\n")
    pass

  def writePush(self, segment:string, index:int, comment=None):
    if comment and self.logLevel>0:
      self.outFile.write(f"push {segment} {index}{self.tab}// {comment}\n")
    else:  
      self.outFile.write(f"{self.tab}push {segment} {index}\n")
    pass
  
  def writePop(self, segment:string, index:int, comment=None):
    if comment and self.logLevel>0:
      self.outFile.write(f"pop {segment} {index}{self.tab}// {comment}\n")
    else:
      self.outFile.write(f"{self.tab}pop {segment} {index}\n")
    pass
    
  def writeFunction(self,name:string, nArgs:int,comment=None):
    if comment and self.logLevel>0:
      self.outFile.write(f"function {name} {nArgs}{self.tab}// {comment}\n")
    else:
      self.outFile.write(f"function {name} {nArgs}\n")

  def writeDecrement(self,segment:string,index:int,comment=None):
    if comment and self.logLevel>0:
      self.outFile.write(f"{self.tab}dec {segment} {index}{self.tab}// {comment}\n")
    else:
      self.outFile.write(f"{self.tab}dec {segment} {index}\n")
    
  def writeIncrement(self,segment:string,index:int,comment=None):
    if comment and self.logLevel>0:
      self.outFile.write(f"{self.tab}inc {segment} {index}{self.tab}// {comment}\n")
    else:
      self.outFile.write(f"{self.tab}inc {segment} {index}\n")