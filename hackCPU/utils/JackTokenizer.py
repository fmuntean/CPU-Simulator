from xml.sax.saxutils import escape


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
    self.children = None
    self.position = -1

  def add(self,tkn):
    if tkn is None: return

    if self.children is None:
      self.children = [tkn]
    else:
      self.children.append(tkn) 
    pass

  def toXml(self,ident=0):
    if self.children is None:
      if self.val is None:
        return f"{' '*ident}<{self.tokenType}>\n{' '*ident}</{self.tokenType}>"
      else:
        return f"{' '*ident}<{self.tokenType}> {escape(self.val)} </{self.tokenType}>"
    
    ret = f"{' '*ident}<{self.tokenType}>\n"
    for child in self.children: 
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

    #accumulate token until whitespace or symbol
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
