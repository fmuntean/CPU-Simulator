class CompilationEngine_lab10:
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
    while self.tknzr.tokenType() == 'comment':
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
    while(tk is not None and tk.tokenType=='comment'):
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
      SymbolTable.add('class',className,'class')
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

    tokenType = self.tknzr.tokenVal()
    tkn = self.eat(['constructor','function','method'],ret)

    if tkn.val in ['void','int','char','boolean'] or tkn.tokenType == 'identifier':
      tkn.tokenType = 'returnType'
      ret.add(tkn)
      tkn=self.nextToken(ret)

    s = SymbolTable.getSymbol('class')
    s.name= s.type+ "."+tkn.val
    s.tokenType = tokenType
    tkn.add(s)
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
  
