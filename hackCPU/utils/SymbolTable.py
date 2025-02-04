# symbol not found is assumed to be either subroutine name or a class name
import string


class Symbol:
  def __init__(self,name:string,type:string,kind:string,index:int):
    self.name  = name
    self.type  = type
    self.kind  = kind
    self.index = index
    self.tokenType = None
    self.children = None
  pass

  def toXml(self,ident=0):
    return f"{' '*ident}<variable name='{self.name}' type='{self.type}' kind='{self.kind}' index={self.index} />"


class SymbolTable:
  first = None
  
  def __init__(self):
    self.symbols=[]
    self.next = None
    pass

  # call every time starting a class or method
  def startScope():
    tbl = SymbolTable()
    tbl.next = SymbolTable.first
    SymbolTable.first = tbl
    pass

  # call every time ending a class or method
  def endScope():
    if SymbolTable.first: 
      SymbolTable.first=SymbolTable.first.next
    pass

  def add(name,type,kind):
    tbl = SymbolTable.first
    index = SymbolTable.varCount(kind)+1
    s = Symbol(name,type,kind,index)
    tbl.symbols.append(s)
    return s

  def varCount(kind):
    tbl = SymbolTable.first
    if len(tbl.symbols)==0:
      return -1
    
    kindList = list(filter(lambda x: x.kind==kind, tbl.symbols))
    return len(kindList)-1  
  
  def getSymbol(name):
    tbl = SymbolTable.first
    while tbl is not None:
      symbol = next(filter(lambda x: x.name==name, tbl.symbols),None)
      if symbol is None:
        tbl = tbl.next
      else:
        return symbol
    return None 





#-------------------------------------------------------------