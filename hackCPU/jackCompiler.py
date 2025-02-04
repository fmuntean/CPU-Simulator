

from csv import Error
import os
from re import A
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
    self.position = -1

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
    return True if self.index+1<=self.len else False

  def getLine(self,tk:Token):
    endPos = self.lines.find('\n',tk.position)
    return self.lines[tk.position:endPos]

  #Gets the current token and advances the input
  def advance(self):
    self.token= Token()
   
    self.token.val = ''
    while(self.index<self.len and self.lines[self.index] in whitespaces): self.index+=1 # skip whitespaces

    self.token.position=self.index
    if self.index>=self.len: 
      return None

    if self.lines[self.index]=='"':
      self.index+=1
      while(self.index<self.len and self.lines[self.index]!='"'):
        self.token.val+=self.lines[self.index]
        self.index+=1
      self.index+=1
      self.token.tokenType = "stringConstant"
      return self.token

    #acumulate token until whitespace or symbol
    while(self.index<=self.len and self.lines[self.index] not in whitespaces and self.lines[self.index] not in symbols):
      self.token.val+=self.lines[self.index]
      self.index+=1
    
    # if no token found we get next character as it could be symbol
    if len(self.token.val)==0:
      if self.index>=self.len:
        self.token = None
        return self.token
      
      self.token.val=self.lines[self.index]
      self.index+=1

      # handling comments
      if self.token.val =='/' and self.lines[self.index]=='/': # we have a comment
        self.token.val = ''
        self.token.tokenType = 'comment'
        self.index+=1
        while(self.index<=self.len and self.lines[self.index]!='\n'):
          self.token.val+=self.lines[self.index]
          self.index+=1
        self.token.position = self.index
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
      
      # handling <= and >= symbols
      if self.token.val in ['<','>'] and self.lines[self.index]=='=':
        self.token.val+='='
        self.index+=1
        self.token.tokenType='symbol'
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
    





class CompilationEngine:
  def __init__(self,tknzr:JackTokenizer, vm:VmWriter):
    self.tknzr = tknzr
    self.vm = vm
    
    self.lbls = {}
    pass

  def getLabel(self,prefix:string):
    if prefix in self.lbls.keys():
      self.lbls[prefix]+=1
    else:
      self.lbls[prefix] = 0
    return f"{self.className}_{self.subrutineName}_{prefix}_{self.lbls[prefix]}"
    
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
      self.className = className
      self.nextToken()
    else:
      raise Exception(tkn)
    
    self.eat('{')
    
    while self.tknzr.tokenVal() in ['static','field']: 
      self.compileClassVarDec()
      
    while self.tknzr.token and  self.tknzr.tokenVal() != '}':
      tk = self.tknzr.token
      self.compileSubroutine(className)

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
  # subroutineBody: '{' varDec* statements '}'
  def compileSubroutine(self, className:string):
    SymbolTable.startScope()

    subType = self.tknzr.tokenVal() #subroutine type: constructor, function, or method 
    tkn = self.eat(['constructor','function','method'])
    if subType == 'method':
        SymbolTable.add('this',className,'argument') # arg0 is THIS

    if tkn.val in ['void','int','char','boolean'] or tkn.tokenType == 'identifier':
      #tkn.tokenType = 'returnType'
      tkn=self.nextToken() #subroutineName

    name = tkn.val  # subroutineName
    
    tkn = self.nextToken()
    self.eat('(')
    self.compileParameterList()
    self.eat(')')

    self.eat('{')
    
    nVars=0
    while self.tknzr.tokenVal() == 'var':
      nVars += self.compileVarDec()
    
    self.vm.writeFunction(f"{className}.{name}",nVars)
    self.subrutineName=name
    if subType=='method':
      #first paramter is THIS
      self.vm.writePush('argument', 0)
      self.vm.writePop('pointer', 0)

    #TODO: implement constructor   
    if subType=='constructor':
      nArgs = len(list(filter(lambda x: x.kind=='this', SymbolTable.first.next.symbols)))
      self.vm.writePush('constant',nArgs)
      self.vm.writeCall('Memory.alloc',1)
      self.vm.writePop('pointer',0)# setting the pointer to the object 

    self.compileStatements()
    
    self.eat('}')
   

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
  
 
  # varDec: 'var' type varName (',' varName)* ';'
  def compileVarDec(self):
    tk = self.eat('var')
    ret =0
    varType = tk.val
    tk = self.nextToken()

    while tk.val != ';':
      if tk.val != ',':
        ret+=1
        SymbolTable.add(tk.val,varType,'local')
      tk = self.nextToken()
    
    self.eat(';')
    return ret



  
  ################################################################
  #               STATEMENTS COMPILATION                         #
  ################################################################
  

  # statements: statement *
  # statement: letStatement | if Statement | whileStatement | doStatement | returnStatement
  def compileStatements(self):
    statements = {
      'let': self.compileLet,
      'do' : self.compileDo,
      'if' : self.compileIf,
      'while': self.compileWhile,
      'return': self.compileReturn
    }
    cmd = self.tknzr.tokenVal()
    while self.tknzr.tokenVal() in statements.keys():
      self.vm.writeComment(self.tknzr.getLine(self.tknzr.token))
      cmd = self.tknzr.tokenVal()
      statements[cmd]()
    return cmd 
  

  # letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
  def compileLet(self): # parses a let statement
    tkn = self.eat('let')
    
    varName = SymbolTable.getSymbol(tkn.val)
    leftExprArray = False
    tkn = self.nextToken()
    if tkn.val=='[':
      leftExprArray = True
      self.eat('[')
      self.compileExpression() 
      self.eat(']')
      self.vm.writePush(varName.kind,varName.index)
      self.vm.writeArithmetic('+')
      
    self.eat('=')

    self.compileExpression()

    

    if leftExprArray:  
      self.vm.writePop('temp',0) # write the result of the expression into temp
      #save left side expression
      self.vm.writePop('pointer',1) # THAT = address of left expression
      self.vm.writePush('temp', 0)  # stack has right expression value
      self.vm.writePop('that',0)    # save right expression value at address of left expression 
    else:
      self.vm.writePop(varName.kind,varName.index)

    self.eat(';')
    return

  # doStatement: 'do' subroutineCall ';'
  # subroutineCall: subroutineName '(' expressionList ')'  |  ( className | varName) '.' subroutineName '(' expressionList ')'
  # expressionList: ( expression ( ',' expression )* )?
  def compileDo(self):
    tkn = self.eat('do')

    self.compileExpression()

    self.eat(';')
    
    self.vm.writePop('temp',0) # we need to extract the return 0 from the do call 
    return

  # ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
  def compileIf(self):
    self.eat('if')
    self.eat('(')
    
    self.compileExpression()

    lbl1 = self.getLabel('if')
    self.vm.writeArithmetic('~')
    self.vm.writeIfGoTo(lbl1)
    
    self.eat(')')
    self.eat('{')
    cmd1 = self.compileStatements()
    if cmd1 !='return':
      lbl2 = self.getLabel('if')
      self.vm.writeGoTo(lbl2)

    tkn = self.eat('}')
    
    self.vm.writeLabel(lbl1)
    if tkn.val == 'else':
      self.eat('else')

      self.eat('{')
      self.compileStatements()
      self.eat('}')
    
    if cmd1!='return':
      self.vm.writeLabel(lbl2)
    return
  
  # whileStatement: 'while' '(' expression ')' '{' statements '}'
  def compileWhile(self): # parses a while statement
    self.eat('while')
    lbl1 = self.getLabel('while')
    self.vm.writeLabel(lbl1)
    self.eat('(')
    self.compileExpression()
    self.eat(')')

    self.vm.writeArithmetic('~')
    lbl2 = self.getLabel('while') 
    self.vm.writeIfGoTo(lbl2)

    self.eat('{')
    self.compileStatements()
    self.eat('}')

    self.vm.writeGoTo(lbl1)
    self.vm.writeLabel(lbl2)
    return
  
  # returnStatement: 'return' expression? ';'
  def compileReturn(self):
    tkn = self.eat('return')
    if tkn.val != ';':
      self.compileExpression()
    else:
      self.vm.writePush("constant",0) # if no return value we need to add one
    self.eat(';')
    self.vm.writeReturn()
    return
  

  ################################################################
  #               EXPRESSION COMPILATION                         #
  ################################################################
  


  # expressionList: ( expression ( ',' expression )* )?
  def compileExpressionList(self):
    ret = 0
    if self.tknzr.tokenVal()==')': # empty expressionList
      return ret
    
    ret+=1
    self.compileExpression()
    
    while self.tknzr.tokenVal()==',':
      ret+=1
      self.eat(',')
      self.compileExpression()
    
    return ret
  
  # expression: term (op term)*
  # op: '+'|'-'|'*'|'/'|'&'|'|'|'<'|'>'|'='
  def compileExpression(self):
    self.compileTerm()
    tk = self.tknzr.token
    op = tk.val
    while op in ['+','-','*','/','&','|','<','>','=','<=','>=']:  # op term
      self.nextToken()
      tk = self.compileTerm()
      self.vm.writeArithmetic(op)
      op=tk.val
    return

  # term: integerConstant | stringConstant | keywordConstant | varName |
  #       varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
  # 
  # subroutineCall: subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')'
  #
  # unaryOp:  '-' | '~'
  def compileTerm(self): # parses a term
    tk = self.tknzr.token

    if tk.tokenType == 'integerConstant': 
      self.vm.writePush('constant',int(tk.val))
      return self.nextToken()

    if tk.tokenType == 'stringConstant':
      self.vm.writePush('constant',len(tk.val))
      self.vm.writeCall('String.new', 1)
      for c in tk.val:
        self.vm.writePush('constant', ord(c),c)
        self.vm.writeCall('String.appendChar',2)
      
      return self.nextToken()  


    if (tk.tokenType=='keyword' and tk.val in ['this','true','false','null']):
      operator = {
        'this':'this',
        'true':1,
        'false':0,
        'null':0
      }[tk.val]
      if operator == 'this':
        self.vm.writePush('pointer',0)
      else:
        self.vm.writePush('constant',operator)
        if tk.val=='true':
          self.vm.writeArithmetic('neg')
      return self.nextToken()

    
    if tk.val in ['-','~']: #unary op
      op = {'-':'neg','~':'~'}[tk.val]
      term = self.nextToken()
      #if term.tokenType=='integerConstant':
      #  self.vm.writePush('constant',int(op+term.val))
      #  self.nextToken()
      #else:
      #  self.compileTerm()
      tk = self.compileTerm()
      self.vm.writeArithmetic(op)
      return tk 

    # varName |  varName '[' expression ']' 
    if tk.tokenType == 'identifier': 
      symbol = SymbolTable.getSymbol(tk.val)
      
      if symbol: #we have varName found
        tk = self.nextToken()
        if tk.val=='[':         # varName '[' expression ']'
          self.eat('[')
          self.compileExpression()
          self.eat(']')
          self.vm.writePush(symbol.kind,symbol.index)
          self.vm.writeArithmetic('+')
          
          self.vm.writePop('pointer', 1) 
          self.vm.writePush('that', 0)
        elif tk.val=='.': # varName '.' subroutineName '(' expressionList ')'
          tk= self.eat('.')
          subrutine = symbol.type+'.'+tk.val
          self.nextToken()
          self.vm.writePush(symbol.kind,symbol.index) #pushing the variable as THIS
          self.eat('(')
          nArgs = self.compileExpressionList()
          tk = self.eat(')')
          self.vm.writeCall(subrutine,nArgs+1)
          return tk
          
        else:
          self.vm.writePush(symbol.kind,symbol.index)

        return self.tknzr.token
      else: # no symbol so handle subroutineCall

        # subroutineCall: subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')'
        subrutine = tk.val
        tk = self.nextToken()
        if tk.val == '.':       # (className | varName) '.' subroutineName '(' expressionList ')'
          tk = self.eat('.')
          subrutine+='.'+tk.val
          tk = self.nextToken()

          self.eat('(')
          nArgs = self.compileExpressionList()
          tk = self.eat(')')
          self.vm.writeCall(subrutine,nArgs)
          return tk
        else:  # subroutineName '(' expressionList ')'
          self.vm.writePush('pointer',0) # first parameter is the pointer to THIS
          self.eat('(')
          nArgs = self.compileExpressionList()
          tk = self.eat(')')
          self.vm.writeCall(self.className+'.'+subrutine,nArgs+1)
          return tk 
   
    tk = self.tknzr.token
    if tk.val =='(':   # '(' expression ')'
      self.eat('(')
      self.compileExpression()
      tk = self.eat(')')
      return tk


    return self.tknzr.token
  



class JackAnalyzer:

  def __init__(self,srcFile:string,vmFile):
    self.tknzr = JackTokenizer(srcFile)
    self.vm = VmWriter(vmFile)
    self.ce = CompilationEngine(self.tknzr,self.vm)
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
  #srcFolder = 'lab11/ConvertToBin'
  #srcFolder = 'lab11/Average'
  #srcFolder = 'lab11/ComplexArrays'
  srcFolder = 'lab11/Pong'
  #srcFolder = 'lab11/Square'
  srcFolder = 'lab12/ArrayTest'
  srcFolder = 'lab12/KeyboardTest'
  srcFolder = 'lab12/MathTest'
  srcFolder = 'lab12/MemoryTest'
  srcFolder = 'lab12/outputtest'
  srcFolder = 'lab12/ScreenTest'
  srcFolder = 'lab12/StringTest'
  

  includeFiles = ['lab12/String.jack','lab12/Output.jack','lab12/Memory.jack','lab12/Sys.jack'] #,'lab12/Screen.jack','lab12/Math.jack'] ,'Lab12/Array.jack','lab12/Keyboard.jack']


  if srcFolder.endswith('.jack'):
    srcFile = srcFolder
    print(f"\n Processing file: {srcFile}\n")
    #tknzr = JackTokenizer(srcFile)
    with open(srcFile[:-4]+'vm',mode='w') as vmFile:
      anlzr = JackAnalyzer(srcFile,vmFile)
      tokens =  anlzr.execute()

  for srcFile in getJackFiles(srcFolder) + includeFiles:
    print(f"\n Processing file: {srcFile}\n")
    #tknzr = JackTokenizer(srcFile)
    vmFile = srcFolder+'/'+srcFile.split('/')[-1][:-4]+'vm'  if srcFile in includeFiles else srcFile[:-4]+'vm' ;
    with open(vmFile,mode='w') as vmFile:
      anlzr = JackAnalyzer(srcFile,vmFile)
      tokens = anlzr.execute()
    
    

  
    
    
    