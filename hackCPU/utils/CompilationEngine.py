import string

from utils.JackTokenizer import JackTokenizer
from utils.SymbolTable import SymbolTable
from utils.VmWriter import VmWriter


class CompilationEngine:
  def __init__(self,tknzr:JackTokenizer, vm:VmWriter,version=1):
    self.tknzr = tknzr
    self.vm = vm
    self.version = version
    self.labels = {}
    pass

  def getLabel(self,prefix:string):
    if prefix in self.labels.keys():
      self.labels[prefix]+=1
    else:
      self.labels[prefix] = 0
    return f"{self.className}_{self.subroutineName}_{prefix}_{self.labels[prefix]}"
    
  def eat(self,ids):
    while self.tknzr.tokenType() == 'comment':
      self.vm.writeComment(self.tknzr.token.val)
      self.nextToken()  

    if self.tknzr.tokenVal() not in ids:
      raise Exception(ids)
    
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
    self.subroutineName=name
    if subType=='method':
      #first parameter is THIS
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
    if self.version==1:
      statements = {
        'let': self.compileLet,
        'do' : self.compileDo,
        'if' : self.compileIf,
        'while': self.compileWhile,
        'return': self.compileReturn
      }
    if self.version==2:
      statements = {
        'let': self.compileLet,
        'do' : self.compileDo_v2,
        'if' : self.compileIf,
        'while': self.compileWhile,
        'return': self.compileReturn_v2
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
  
  def compileDo_v2(self):
    tkn = self.eat('do')

    self.compileExpression()

    self.eat(';')
    
    self.vm.writeDecrement('SP',0) # we just decrement SP as we do not need the value
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
  
   # returnStatement: 'return' expression? ';'
  def compileReturn_v2(self):
    tkn = self.eat('return')
    if tkn.val != ';':
      self.compileExpression()
    else:
      self.vm.writeIncrement('SP',0) # we just increment SP as we don't care whats inside
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
          subroutine = symbol.type+'.'+tk.val
          self.nextToken()
          self.vm.writePush(symbol.kind,symbol.index) #pushing the variable as THIS
          self.eat('(')
          nArgs = self.compileExpressionList()
          tk = self.eat(')')
          self.vm.writeCall(subroutine,nArgs+1)
          return tk
          
        else:
          self.vm.writePush(symbol.kind,symbol.index)

        return self.tknzr.token
      else: # no symbol so handle subroutineCall

        # subroutineCall: subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')'
        subroutine = tk.val
        tk = self.nextToken()
        if tk.val == '.':       # (className | varName) '.' subroutineName '(' expressionList ')'
          tk = self.eat('.')
          subroutine+='.'+tk.val
          tk = self.nextToken()

          self.eat('(')
          nArgs = self.compileExpressionList()
          tk = self.eat(')')
          self.vm.writeCall(subroutine,nArgs)
          return tk
        else:  # subroutineName '(' expressionList ')'
          self.vm.writePush('pointer',0) # first parameter is the pointer to THIS
          self.eat('(')
          nArgs = self.compileExpressionList()
          tk = self.eat(')')
          self.vm.writeCall(self.className+'.'+subroutine,nArgs+1)
          return tk 
   
    tk = self.tknzr.token
    if tk.val =='(':   # '(' expression ')'
      self.eat('(')
      self.compileExpression()
      tk = self.eat(')')
      return tk


    return self.tknzr.token
  
