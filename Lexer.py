import yaml, re

#Token class for keeping track of type, value, and scope
class Token (object):
  def __init__(self, type, value, scope):
    self.type       = type
    self.value      = value
    self.scope      = scope

  def __str__(self):
    return 'Token(type="{type}", value="{val}", scope="{scope}")'.format(
      type = self.type,
      val  = self.value,
      scope= self.scope
    )
    
  def __repr__(self):
    return self.__str__()
    
    
class Lexer (object):
  def __init__(self, text, config):
    #Format text
    self.text     = text.replace('\t','  ')
    self.text     = self.text.split('\n')
    
    # Initialize
    self.config   = config
    self.lineInd  = 0
    self.charInd  = 0
    self.numLines = len(self.text)
    self.complete = False
    self.scope    = 0
    self.tabWidth = config['tabWidth']
    
    #Get token and keyword list from config
    self.tokens   = self.config['tokens']
    self.keywords = self.config['keywords']
    
    #Debug
    print(text)
    print('numLines = {0}'.format(self.numLines))
    
  def advanceIndex(self, matchStr):
    matchLen = len(matchStr)
    currLineLen = len(self.text[self.lineInd])
    
    # Increment charInd and lineInd if necessary
    if ((self.charInd + matchLen) < currLineLen):
      self.charInd += matchLen
    else:
      self.lineInd += 1
      self.charInd = 0
      
      #Check if entire text has been parsed
      if len(self.text) == self.lineInd:
        self.complete = True
        return 'EOF'
      else:
        return 'EOL'
        
    return None
        
  def matchWhiteSpace(self):
    #Get Str
    lineStr = self.text[self.lineInd][self.charInd:]
    
    #Find whitespace first
    matchObj = re.match('\s+',lineStr)
    
    #if lineStr is empty, report EOL
    if not lineStr:
      ws = self.advanceIndex(lineStr)
      return Token(ws,None,None)
    
    #if WS was found, advance and check EOL EOF
    elif (matchObj):
      matchStr = matchObj.group(0)
      #Check scope if charInd == 0
      if self.charInd == 0:
        #TODO: Need better scoping in future
        self.scope = len(matchStr)/self.tabWidth
      
      ws = self.advanceIndex(matchStr)
      if ws is not None:
        return Token(ws,None,None)
        
    # No WS but not EOL, EOF. Can only be scope = 0
    if self.charInd == 0:
      #TODO: Need better scoping in future
      self.scope = 0
    
    #Removed whitespace, but not EOL or EOF token
    return None

      
  def matchKeywords(self, matchStr):
    #Check IDs if they are keywords
    for keyword in self.keywords:
      if matchStr == keyword['regex']:
        return keyword['type']
    
    # No match found, must be ID
    return None
    
  def get_next_token(self):
    #Return EOF if lexer reached end of text
    if self.complete:
      return Token('EOF',None,None)
    
    wsToken = self.matchWhiteSpace()
    if wsToken:
      return wsToken
      
    #Get String
    lineStr = self.text[self.lineInd][self.charInd:]
      
    #Match tokens from config
    for token in self.tokens:
      regexPattern = '('+ token['regex'] + ')'
      matchObj = re.match(regexPattern, lineStr)
      if matchObj:
        # match string
        matchStr = matchObj.group(0)
        
        # for token 'ID', match against keywords
        if (token['type'] == 'ID'):
          keyword = self.matchKeywords(matchStr)
          if keyword:
            token = Token(keyword, matchStr, self.scope)
          else:
            token = Token(token['type'], matchStr, self.scope)
        else:
          token = Token(token['type'], matchStr, self.scope)
        self.charInd += len(matchStr)
        return token
    
    #Token not found, exception
    raise Exception('Invalid character "{0}"'.format(re.match('(\S*)',lineStr).group(0)))
    
    
def main():
  #Load Lexer Configuration
  fo = open('grammer-fdl.yaml')
  lexerConfig = yaml.load(fo.read())
  fo.close()
  
  #Test String
  fo = open('example.fdl')
  testStr = fo.read()
  fo.close()
  
  #Initialize Lexer
  lexer = Lexer(testStr, lexerConfig)
  
  # Loop over text until EOF found
  token = lexer.get_next_token()
  print('Found! {0}'.format(token))
  while (token.type != 'EOF'):
    token = lexer.get_next_token()
    print('Found! {0}'.format(token))
    
    
if __name__ == '__main__':
  main()