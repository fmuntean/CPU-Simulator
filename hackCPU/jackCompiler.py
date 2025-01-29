

from csv import Error
import os
import string
from symtable import SymbolTable
from xml.sax.saxutils import escape

from sympy import Symbol

import vm_commands


keywords =['class','constructor','function','method','field','static','var','int','char',
          'boolean','void','true','false','null','this','let','do','if','else','while','return']

symbols= ['{','}','(',')','[',']','.',',',';','+','-','*','/','&','|','<','>','=','~']

whitespaces = [ ' ', '\n', '\t','\r']



#integerConstant: a decimal number in the range 0 ... 32767
#StringConstant: '"' a sequence of characters '"'(not including double quote or newline)
#identifier: a sequence of letters, digits, and underscore ( '_' ) not starting with a digit.

class Token:
  def __init__(self,tokenType=None,tokenVal=None):
    self.tokenType = tokenType
    self.val = tokenVal
    self.childrens = None

  def add(self,tkn):
    if tkn is None: return

    if self.childrens is None:
      self.childrens = [tkn]
    else:
      self.childrens.append(tkn) 
    pass

  def toXml(self,ident=0):
    if self.childrens is None:
      if self.val is None:
        return f"{' '*ident}<{self.tokenType}>\n{' '*ident}</{self.tokenType}>"
      else:
        return f"{' '*ident}<{self.tokenType}> {escape(self.val)} </{self.tokenType}>"
    
    ret = f"{' '*ident}<{self.tokenType}>\n"
    for child in self.childrens: 
      if child is None: continue
      ret+=child.toXml(ident+2)
      ret+='\n'
    ret+=f"{' '*ident}</{self.tokenType}>"
    return ret
  


class JackTokenizer:
  def __init__(self,src):
    with open(src,mode='r') as f:
      self.lines = '\n'.join(f.readlines())
    self.index = 0
    self.len = len(self.lines)
    pass
  


  #Checks if there are more lines to process
  def hasMoreTokens(self):
    return True if self.index+1<self.len else False

  #Gets the current token and advances the input
  def advance(self):
    self.token= Token()
    self.token.val = ''
    while(self.index<self.len and self.lines[self.index] in whitespaces): self.index+=1 # skip whitespaces

    if self.index==self.len: return None

    if self.lines[self.index]=='"':
      self.index+=1
      while(self.index<self.len and self.lines[self.index]!='"'):
        self.token.val+=self.lines[self.index]
        self.index+=1
      self.index+=1
      self.token.tokenType = "stringConstant"
      return self.token

    #acumulate token until whitespace or symbol
    while(self.index<self.len and self.lines[self.index] not in whitespaces and self.lines[self.index] not in symbols):
      self.token.val+=self.lines[self.index]
      self.index+=1
    
    # if no token found we get next character as it could be symbol
    if len(self.token.val)==0:
      if self.index+1>=self.len:
        self.token = None
        return self.token
      self.token.val=self.lines[self.index]
      self.index+=1
      if self.token.val =='/' and self.lines[self.index]=='/': # we have a comment
        self.token.val = ''
        self.token.tokenType = 'comment'
        self.index+=1
        while(self.index<self.len and self.lines[self.index]!='\n'):
          self.token.val+=self.lines[self.index]
          self.index+=1
        return self.token
      elif self.token.val == '/' and self.lines[self.index]=='*': # we have multiline comment
        self.token.val = ''
        self.token.tokenType = 'comment'
        self.index+=1
        while(self.index<self.len and self.lines[self.index:self.index+2]!='*/'):
          self.token.val+=self.lines[self.index]
          self.index+=1
        self.index+=2
        return self.token
       
    #identify the token type
    if (self.token.val in symbols):
      self.token.tokenType = 'symbol'
    elif (self.token.val in keywords):
      self.token.tokenType = 'keyword'
    elif self.token.val[0] in ['0','1','2','3','4','5','6','7','8','9']:
      self.token.tokenType = 'integerConstant'
      #self.token.val = int(self.token.val)
    else:
      self.token.tokenType = 'identifier'
    return self.token

  #Returns the type of the current token
  def tokenType(self):
    return self.token.tokenType
  
  def tokenVal(self):
    return self.token.val



class VmWriter:
  

  def __init__(self, outFile):
    self.outFile = outFile
    pass

  def writeComment(self,msg:string):
    self.outFile.write(f"/* {msg} */\n")

  def writeGoTo(self,lbl:string):
    self.outFile.write(f"goto {lbl}\n")

  def writeGoTo(self,lbl:string):
    self.outFile.write(f"if-goto {lbl}\n")

  def writeCall(self,lbl:string, nArgs:int):
    self.outFile.write(f"call {lbl} {nArgs}\n")

  def writeLabel(self,lbl:string):
    self.outFile.write(f"label {lbl}\n")
  
  def writeArithmetic(self,op):
    operations = {
      '+': 'add',
      '-': 'sub',
      '*': 'call Math.multiply 2', 
      '/': 'call Math.divide 2',
      '&': 'and',
      '|': 'or',
      '<': 'lt',
      '>': 'gt',
      '=': 'eq'
    }
    self.outFile.write(f"{operations[op]}\n")
  
  def writeReturn(self):
    self.outFile.write(f"return\n")
    pass

  def writePush(self, segment:string, index:int):
    self.outFile.write(f"push {segment} {index}\n")
    pass
  
  def writePop(self, segment:string, index:int):
    self.outFile.write(f"pop {segment} {index}\n")
    pass
    
  def writeFunction(self,name:string, nArgs:int):
    self.outFile.write(f"function {name} {nArgs}\n")






class CompilationEngine:
  def __init__(self,tknzr:JackTokenizer, vm:VmWriter):
    self.tknzr = tknzr
    self.vm = vm
    self.statements = {
      'let': self.compileLet,
      'do' : self.compileDo,
      'if' : self.compileIf,
      'while': self.compileWhile,
      'return': self.compileReturn
    }

  def eat(self,ids):
    while self.tknzr.tokenType() == 'comment':
      self.vm.writeComment(self.tknzr.token.val)
      self.nextToken()  

    if self.tknzr.tokenVal() not in ids:
      raise Error(ids)
    
    ret = self.nextToken()
    return ret
    
  def nextToken(self):
    '''
      returns next token and add comments to the specified token
    '''
    tk=self.tknzr.advance()
    while(tk is not None and tk.tokenType=='comment'):
      self.vm.writeComment(tk.val)
      tk=self.tknzr.advance()
    return tk
  
  
  # class: 'class' className '{' classVarDec* subroutineDec* '}'
  def compileClass(self): # parses class statement
    SymbolTable.startScope()

    tkn =  self.eat('class')
    if tkn.tokenType=='identifier':
      className = tkn.val
      #SymbolTable.add('class',className,'class')
      self.nextToken()
    else:
      raise Exception(tkn)
    
    self.eat('{')
    
    while self.tknzr.tokenVal() in ['static','field']: 
      self.compileClassVarDec()
      
    while self.tknzr.tokenVal() != '}':
      tk = self.tknzr.token
      if tk.val == 'method':
        SymbolTable.add('this',className,'argument')
      self.compileSubroutineDec(className)

    self.eat('}')
    SymbolTable.endScope()
    return

  # classVarDec: ('static'|'field') type varName (',' varName)* ';'
  def compileClassVarDec(self):
    kind = self.tknzr.tokenVal().replace('field','this')
    
    tk = self.eat(['static','field'])

    varType = tk.val 
    tk= self.nextToken()

    while tk.val !=';':
      if tk.val!=',':
        tk.add(SymbolTable.add(tk.val,varType,kind))
        
      tk=self.nextToken() 

    self.eat(';')
    return

  # subroutineDec: ('constructor'|'function'|'method') ('void'|type) subroutineName '(' parameterList ')' subroutineBody
  # type: 'int'|'char'|'boolean'|className
  def compileSubroutineDec(self, className:string):
    SymbolTable.startScope()

    tokenType = self.tknzr.tokenVal()
    tkn = self.eat(['constructor','function','method'])

    if tkn.val in ['void','int','char','boolean'] or tkn.tokenType == 'identifier':
      #tkn.tokenType = 'returnType'
      tkn=self.nextToken() #subroutineName

    name = tkn.val
    
    #s = SymbolTable.getSymbol('class')
    #s.name= s.type+ "."+tkn.val
    #s.tokenType = tokenType
    #ret.add(tkn) # subroutineName
    
    tkn = self.nextToken()
    self.eat('(')

    self.compileParameterList()
    
    nArgs = SymbolTable.varCount('argument')+1
    self.vm.writeFunction(f"{className}.{name}",nArgs)
      
    self.eat(')')

    self.compileSubroutineBody()
    
    SymbolTable.endScope()
    return


  # parameterList: ( (type varName) (',' type varName)* )?
  def compileParameterList(self):
    while self.tknzr.tokenVal() != ')':
      tk = self.tknzr.token
      varType = tk.val     
      #ret.add(tk) #type
      
      tk = self.nextToken() # varName
      SymbolTable.add(tk.val,varType,'argument')
      
      tk = self.nextToken()
      if tk.val==',':
        self.eat(',')
      
    return
  
  #subroutineBody: '{' varDec* statements '}'
  def compileSubroutineBody(self):
    self.eat('{')

    while self.tknzr.tokenVal() == 'var':
      self.compileVarDec()
      
    self.compileStatements()
    
    self.eat('}')
    return

  # varDec: 'var' type varName (',' varName)* ';'
  def compileVarDec(self):
    tk = self.eat('var')

    varType = tk.val
    tk = self.nextToken()

    while tk.val != ';':
      if tk.val != ',':
        SymbolTable.add(tk.val,varType,'local')
      tk = self.nextToken()
    
    self.eat(';')
    return



  
  ################################################################
  #               STATEMENTS COMPILATION                         #
  ################################################################
  

  # statements: statement *
  # statement: letStatement | if Statement | whileStatement | doStatement | returnStatement
  def compileStatements(self):
    while self.tknzr.tokenVal() in self.statements.keys():
      self.statements[self.tknzr.tokenVal()]()
    return
  

  # letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
  def compileLet(self): # parses a let statement
    tkn = self.eat('let')
    
    varName = SymbolTable.getSymbol(tkn.val)
    
    tkn = self.nextToken()
    if tkn.val=='[':
      self.eat('[')
      self.compileExpression(']') 
      self.eat(']')

    
    self.eat('=')

    self.compileExpression(';')
    
    self.eat(';')  
    return

  # doStatement: 'do' subroutineCall ';'
  # subroutineCall: subroutineName '(' expressionList ')'  |  ( className | varName) '.' subroutineName '(' expressionList ')'
  # expressionList: ( expression ( ',' expression )* )?
  def compileDo(self):
    tkn = self.eat('do')

    if tkn.tokenType=='identifier':
      symbol = SymbolTable.getSymbol(tkn.val)  # subroutineName or className or varName
      name = symbol.name if symbol else tkn.val
    tk = self.nextToken()
    if tk.val == '(': #expressionlist
      self.eat('(')
      nArgs = self.compileExpressionList(')')
      self.eat(')')
    else:
      tk=self.eat('.')
      name+='.'+tk.val
      #ret.add(tk) #subroutineName
      self.nextToken()
      self.eat('(')
      nArgs = self.compileExpressionList(')')
      self.eat(')')

    self.eat(';')
    self.vm.writeCall(name,nArgs)
    self.vm.writePop('local',0) # we need to extract the return 0 from the do call 
    return

  # ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
  def compileIf(self):
    self.eat('if')
    self.eat('(')
    
    self.compileExpression(')')
    
    self.eat(')')
    self.eat('{')
    self.compileStatements()
    
    tkn = self.eat('}')
    if tkn.val == 'else':
      self.eat('else')
      self.eat('{')
      self.compileStatements()
      self.eat('}')

    return
  
  # whileStatement: 'while' '(' expression ')' '{' statements '}'
  def compileWhile(self): # parses a while statement
    self.eat('while')
    self.eat('(')

    self.compileExpression(')')
    self.eat(')')

    self.eat('{')
    self.compileStatements()

    self.eat('}')

    return
  
  # returnStatement: 'return' expression? ';'
  def compileReturn(self):
    tkn = self.eat('return')
    if tkn.val != ';':
      self.compileExpression(';')
    else:
      self.vm.writePush("constant",0) # if no return value we need to add one
    self.eat(';')
    self.vm.writeReturn()
    return
  

  ################################################################
  #               EXPRESSION COMPILATION                         #
  ################################################################
  


  # expressionList: ( expression ( ',' expression )* )?
  def compileExpressionList(self,end):
    ret = 0
    if self.tknzr.tokenVal()==')': # empty expressionList
      return ret
    
    ret+=1
    self.compileExpression([',',end])
    
    while self.tknzr.tokenVal()==',':
      ret+=1
      self.eat(',')
      self.compileExpression([',',end])
    
    return ret
  
  # expression: term (op term)*
  # op: '+'|'-'|'*'|'/'|'&'|'|'|'<'|'>'|'='
  def compileExpression(self, end):
    self.compileTerm()
    tk = self.tknzr.token
    op = tk.val
    while tk.val in ['+','-','*','/','&','|','<','>','=']:  # op term
      tk = self.nextToken()
      self.compileTerm()
      self.vm.writeArithmetic(op)
      
    return

  # term: integerConstant | stringConstant | keywordConstant | varName |
  #       varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
  # 
  # subroutineCall: subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')'
  #
  # unaryOp:  '-' | '~'
  def compileTerm(self): # parses a term
    if self.tknzr.tokenVal() =='(':   #'(' expression ')'
      self.eat('(')
      self.compileExpression(')')
      self.eat(')')
      return
   
    if self.tknzr.tokenVal() in ['-','~']:
      self.nextToken()
      self.compileTerm()
      return

    if (self.tknzr.tokenType() in ['stringConstant', 'integerConstant', 'identifier']) \
       or (self.tknzr.tokenType()=='keyword' and self.tknzr.tokenVal() in ['this','true','false','null']):
      
      tk = self.tknzr.token
      if tk.tokenType=='identifier':
        symbol = SymbolTable.getSymbol(tk.val)
      else:
        self.vm.writePush('constant',tk.val)


      tk = self.nextToken()
      if tk.val=='[':         # varName '[' expression ']'
        self.eat('[')
        self.compileExpression(']')
        self.eat(']')
        return
      
      if tk.val=='(':         # subroutineName '(' expressionList ')'
        self.eat('(')
        self.compileExpressionList(')')
        self.eat(')')
        return

      if tk.val == '.':       # (className | varName) '.' subroutineName '(' expressionList ')'
        tk = self.eat('.')
        #ret.add(tk)  # subroutineName
        
        self.nextToken()
        self.eat('(')
        tk = self.compileExpressionList(')')
        self.eat(')')
        return

    return
  



class JackAnalyzer:

  def __init__(self,srcFile:string,vmFile):
    self.tknzr = JackTokenizer(srcFile)
    self.vm = VmWriter(vmFile)
    self.ce = CompilationEngine(self.tknzr,self.vm)
    self.srcFile = srcFile

  #Version 0: Designed to test the JackTokenizer
  def extractTokens(self):
    self.ce.nextToken(); # gets the first token
    while self.tknzr.hasMoreTokens():
      token = self.tknzr.getToken()
      if token is not None:
        print(token.toXml())
        self.nextToken()


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

# symbol not found is assumed to be either subroutine name or a class name
class Symbol:
  def __init__(self,name:string,type:string,kind:string,index:int):
    self.name  = name
    self.type  = type
    self.kind  = kind
    self.index = index
    self.tokenType = None
    self.childrens = None
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
def getJackFiles(srcFoolder:string):
  ret =[]
   # r=root, d=directories, f = files
  for r, d, f in os.walk(srcFolder):
    for file in f:
      if file.endswith(".jack"):
          ret.append(os.path.join(r, file))
  return ret


if __name__ == '__main__':
  srcFolder = 'Lab10/ArrayTest' #argv[1]
  srcFolder = 'lab10/ExpressionLessSquare'
  srcFolder = 'lab10/Square'
  srcFolder = 'lab11/Seven'
  
  for srcFile in getJackFiles(srcFolder):
    print(f"\n Processing file: {srcFile}\n")
    #tknzr = JackTokenizer(srcFile)
    with open(srcFile[:-4]+'vm',mode='w') as vmFile:
      anlzr = JackAnalyzer(srcFile,vmFile)
      tokens = anlzr.execute()

    
    