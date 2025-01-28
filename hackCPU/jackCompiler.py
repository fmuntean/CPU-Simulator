

from csv import Error
import os
import string
from symtable import SymbolTable
from xml.sax.saxutils import escape

from sympy import Symbol


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
        self.token.tokenType = 'COMMENT'
        self.index+=1
        while(self.index<self.len and self.lines[self.index]!='\n'):
          self.token.val+=self.lines[self.index]
          self.index+=1
        return self.token
      elif self.token.val == '/' and self.lines[self.index]=='*': # we have multiline comment
        self.token.val = ''
        self.token.tokenType = 'COMMENT'
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








class CompilationEngine:
  def __init__(self,tknzr:JackTokenizer):
    self.tknzr = tknzr
    self.statements = {
      'let': self.compileLet,
      'do' : self.compileDo,
      'if' : self.compileIf,
      'while': self.compileWhile,
      'return': self.compileReturn
    }

  def eat(self,ids,toToken=None):
    while self.tknzr.tokenType() == 'COMMENT':
      if toToken: toToken.add(self.tknzr.token)
      self.nextToken(toToken)  

    if self.tknzr.tokenVal() not in ids:
      raise Error(ids)
    
    if toToken: toToken.add(self.tknzr.token)
    ret = self.nextToken(toToken)
    return ret
    
  def nextToken(self,token=None):
    '''
      returns next token and add comments to the specified token
    '''
    tk=self.tknzr.advance()
    while(tk is not None and tk.tokenType=='COMMENT'):
      if token: token.add(tk)
      tk=self.tknzr.advance()
    return tk
  
  
  # class: 'class' className '{' classVarDec* subroutineDec* '}'
  def compileClass(self): # parses class statement
    SymbolTable.startScope()

    ret = Token('class')
    tkn =  self.eat('class',ret)

    if tkn.tokenType=='identifier':
      ret.add(tkn)
      className = tkn.val
      self.nextToken(ret)
    else:
      raise Exception(tkn)
    
    self.eat('{',ret)
    
    while self.tknzr.tokenVal() in ['static','field']: 
      tkn = self.compileClassVarDec()
      if tkn: ret.add(tkn)

    while self.tknzr.tokenVal() != '}':
      tk = self.tknzr.token
      if tk.val == 'method':
        SymbolTable.add('this',className,'argument')
      tkn = self.compileSubroutineDec()
      if tkn: ret.add(tkn)

    self.eat('}',ret)
    SymbolTable.endScope()
    return ret

  # classVarDec: ('static'|'field') type varName (',' varName)* ';'
  def compileClassVarDec(self):
    ret = Token('classVarDec')
    
    kind = self.tknzr.tokenVal().replace('field','this')
    
    tk = self.eat(['static','field'],ret)

    varType = tk.val 
    tk= self.nextToken(ret)

    while tk.val !=';':
      if tk.val!=',':
        tk.add(SymbolTable.add(tk.val,varType,kind))
        
      ret.add(tk)
      tk=self.nextToken(ret) 

    self.eat(';',ret)
    return ret

  # subroutineDec: ('constructor'|'function'|'method') ('void'|type) subroutineName '(' parameterList ')' subroutineBody
  # type: 'int'|'char'|'boolean'|className
  def compileSubroutineDec(self):
    SymbolTable.startScope()

    ret = Token('subroutineDec')

    tkn = self.eat(['constructor','function','method'],ret)

    if tkn.val in ['void','int','char','boolean'] or tkn.tokenType == 'identifier':
      ret.add(tkn)
      tkn=self.nextToken(ret)

    ret.add(tkn) # subroutineName
    
    tkn = self.nextToken(ret)
    self.eat('(',ret)

    tkn = self.compileParameterList()
    if tkn: ret.add(tkn)

    self.eat(')',ret)

    tkn = self.compileSubroutineBody()
    if tkn: ret.add(tkn)

    SymbolTable.endScope()
    return ret



  # parameterList: ( (type varName) (',' type varName)* )?
  def compileParameterList(self):
    ret = Token('parameterList')

    while self.tknzr.tokenVal() != ')':
      tk = self.tknzr.token
      varType = tk.val     
      #ret.add(tk) #type
      
      tk = self.nextToken(ret) # varName
      tk.add(SymbolTable.add(tk.val,varType,'argument'))
      ret.add(tk)

      tk = self.nextToken(ret)
      if tk.val==',':
        self.eat(',')
      
    return ret    
  
  #subroutineBody: '{' varDec* statements '}'
  def compileSubroutineBody(self):
    ret = Token('subroutineBody')
    self.eat('{',ret)

    while self.tknzr.tokenVal() == 'var':
      tkn = self.compileVarDec()
      if tkn: ret.add(tkn)

    tkn = self.compileStatements()
    if tkn: ret.add(tkn)

    self.eat('}',ret)
    return ret

  # varDec: 'var' type varName (',' varName)* ';'
  def compileVarDec(self):
    ret = Token('varDec')
    tk = self.eat('var',ret)

    varType = tk.val
    tk = self.nextToken(ret)

    while tk.val != ';':
      if tk.val != ',':
        tk.add(SymbolTable.add(tk.val,varType,'local'))
      ret.add(tk)
      tk = self.nextToken(ret)
    
    ret.add(self.tknzr.token)
    self.eat(';')
    return ret



  
  ################################################################
  #               STATEMENTS COMPILATION                         #
  ################################################################
  

  # statements: statement *
  # statement: letStatement | if Statement | whileStatement | doStatement | returnStatement
  def compileStatements(self):
    ret = Token('statements')
    while self.tknzr.tokenVal() in self.statements.keys():
      tkn = self.statements[self.tknzr.tokenVal()]()
      if tkn: ret.add(tkn)
    return ret
  

  # letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
  def compileLet(self): # parses a let statement
    ret = Token('letStatement')
    tkn = self.eat('let',ret)
    
    tkn.add(SymbolTable.getSymbol(tkn.val))
    ret.add(tkn) # varName

    tkn = self.nextToken(ret)
    if tkn.val=='[':
      self.eat('[',ret)
      tkn = self.compileExpression(']') 
      if tkn: ret.add(tkn)
      self.eat(']',ret)

    
    self.eat('=',ret)

    tkn = self.compileExpression(';')
    if tkn: ret.add(tkn)

    self.eat(';',ret)  

    return ret

  # doStatement: 'do' subroutineCall ';'
  # subroutineCall: subroutineName '(' expressionList ')'  |  ( className | varName) '.' subroutineName '(' expressionList ')'
  # expressionList: ( expression ( ',' expression )* )?
  def compileDo(self):
    ret = Token('doStatement')
    tkn = self.eat('do',ret)

    if tkn.tokenType=='identifier':
      symbol = SymbolTable.getSymbol(tkn.val)
      if symbol: tkn.add(symbol)
    ret.add(tkn) # subroutineName or className or varName

    tk = self.nextToken()
    if tk.val == '(': #expressionlist
      self.eat('(',ret)
      tk = self.compileExpressionList(')')
      if tk: ret.add(tk)
      self.eat(')',ret)
    else:
      tk = self.eat('.',ret)
      ret.add(tk) #subroutineName
      self.nextToken()
      self.eat('(',ret)
      tk = self.compileExpressionList(')')
      if tk: ret.add(tk)
      self.eat(')',ret)

    
    
    #while tkn.val != ';':
    #  ret.add(tkn)
    #  tkn = self.nextToken(ret)
    
    self.eat(';',ret)
    return ret

  # ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
  def compileIf(self):
    ret = Token('ifStatement')
    self.eat('if',ret)
    self.eat('(',ret)
    
    tkn = self.compileExpression(')')
    ret.add(tkn)

    self.eat(')',ret)
    self.eat('{',ret)
    tkn = self.compileStatements()
    ret.add(tkn)

    tkn = self.eat('}',ret)
    if tkn.val == 'else':
      self.eat('else',ret)
      self.eat('{',ret)
      tkn = self.compileStatements()
      ret.add(tkn)
      self.eat('}',ret)

    return ret
  
  # whileStatement: 'while' '(' expression ')' '{' statements '}'
  def compileWhile(self): # parses a while statement
    ret = Token('whileStatement')
    
    self.eat('while',ret)
    self.eat('(',ret)

    tkn = self.compileExpression(')')
    ret.add(tkn)
    self.eat(')',ret)

    self.eat('{',ret)
    tkn = self.compileStatements()
    ret.add(tkn)

    self.eat('}',ret)

    return ret
  
  # returnStatement: 'return' expression? ';'
  def compileReturn(self):
    ret = Token('returnStatement')
    tkn = self.eat('return',ret)
    if tkn.val != ';':
      tkn = self.compileExpression(';')
      ret.add(tkn)
    
    self.eat(';',ret)
    return ret

  

  ################################################################
  #               EXPRESSION COMPILATION                         #
  ################################################################
  


  # expressionList: ( expression ( ',' expression )* )?
  def compileExpressionList(self,end):
    ret = Token('expressionList')
    
    if self.tknzr.tokenVal()==')': # empty expressionList
      return ret
    
    tk = self.compileExpression([',',end])
    ret.add(tk)

    while self.tknzr.tokenVal()==',':
      self.eat(',',ret)
      tk = self.compileExpression([',',end])
      ret.add(tk)
  
    return ret
  
  # expression: term (op term)*
  # op: '+'|'-'|'*'|'/'|'&'|'|'|'<'|'>'|'='
  def compileExpression(self, end):
    #TODO: implement expression for now we just read until end token is found
    ret = Token('expression')
    
    tk = self.compileTerm()
    ret.add(tk)
    
    tk = self.tknzr.token
    while tk.val in ['+','-','*','/','&','|','<','>','=']:  # op term
      ret.add(tk)
      self.nextToken()
      tk = self.compileTerm()
      ret.add(tk)

    return ret

  # term: integerConstant | stringConstant | keywordConstant | varName |
  #       varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
  # 
  # subroutineCall: subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')'
  #
  # unaryOp:  '-' | '~'
  def compileTerm(self): # parses a term
    ret = Token('term')
    if self.tknzr.tokenVal() =='(':   #'(' expression ')'
      self.eat('(',ret)
      tk = self.compileExpression(')')
      ret.add(tk)
      self.eat(')',ret)
      return ret
    
    #if self.tknzr.tokenType()=='keyword' and self.tknzr.tokenVal() in ['this']:
    #  ret.add(self.tknzr.token)
    #  tk = self.nextToken()

    if self.tknzr.tokenVal() in ['-','~']:
      ret.add(self.tknzr.token)
      self.nextToken()
      tk = self.compileTerm()
      ret.add(tk)
      return ret

    if (self.tknzr.tokenType() in ['stringConstant', 'integerConstant', 'identifier']) \
       or (self.tknzr.tokenType()=='keyword' and self.tknzr.tokenVal() in ['this','true','false','null']):
      
      tk = self.tknzr.token
      if tk.tokenType=='identifier':
        tk.add(SymbolTable.getSymbol(tk.val))
      ret.add(tk)
      tk = self.nextToken()
      
      if tk.val=='[':         # varName '[' expression ']'
        self.eat('[',ret)
        tk = self.compileExpression(']')
        ret.add(tk)
        self.eat(']',ret)
        return ret
      
      if tk.val=='(':         # subroutineName '(' expressionList ')'
        self.eat('(',ret)
        tk = self.compileExpressionList(')')
        ret.add(tk)
        self.eat(')',ret)
        return ret

      if tk.val == '.':       # (className | varName) '.' subroutineName '(' expressionList ')'
        tk = self.eat('.',ret)
        ret.add(tk)  # subroutineName
        
        self.nextToken(ret)
        self.eat('(',ret)
        tk = self.compileExpressionList(')')
        ret.add(tk)
        self.eat(')',ret)
        return ret

    return ret
  



class JackAnalyzer:

  def __init__(self,srcFile:string):
    self.tknzr = JackTokenizer(srcFile)
    self.ce = CompilationEngine(self.tknzr)
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
    xmlFile = self.srcFile[:-4]+'xml'
    with open(xmlFile,mode='w') as xml:
      self.ce.nextToken(); # gets the first token
      token = self.tknzr.token
      while (token.tokenType!='keyword'):
        if token.tokenType == 'COMMENT':
          xml.write(token.toXml())
          xml.write('\n')
          self.ce.nextToken()
          token = self.tknzr.token
        else:
          print (f"ERROR: invalid token")
          print(token.toXml())

      token = self.ce.compileClass()
      
      xml.write(token.toXml())
  
#------------------------------------------------------------

# symbol not found is assumed to be either subroutine name or a class name
class Symbol:
  def __init__(self,name:string,type:string,kind:string,index:int):
    self.name  = name
    self.type  = type
    self.kind  = kind
    self.index = index
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




class VmWriter:
  def __init__(self):
    pass


  def writePush():
    pass
  def writePop():
    pass
    

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
  
  for srcFile in getJackFiles(srcFolder):
    print(f"\n Processing file: {srcFile}\n")
    #tknzr = JackTokenizer(srcFile)
    anlzr = JackAnalyzer(srcFile)
    anlzr.execute()
  #  with open(srcFile,mode="r") as f:
  #    _,sourceFile=os.path.split(srcFile)
  #    
    