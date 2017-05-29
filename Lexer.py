import yaml, re


lexerConfigStr ="""
grammer: FDL
author: Aaron Woody
tokens:
  - regex:   '[a-zA-Z][a-zA-Z0-9_]*'
    type:    ID
  - regex:   '[0-9]+'
    type:    INTEGER
  - regex:   '='
    type:    ASSIGN
  - regex:   '\('
    type:    LPAREN
  - regex:   '\)'
    type:    RPAREN
  - regex:   ':'
    type:    COLON
  - regex:   ','
    type:    COMMA
keywords:
  - regex:   module
    type:    MODULE
  - regex:   in
    type:    INTERFACE
  - regex:   out
    type:    INTERFACE
  - regex:   '='
    type:    ASSIGN
  - regex:   and
    type:    OPER
  - regex:   or
    type:    OPER
"""

class Token (object):
  def __init__(self, type, value):
    self.type       = type
    self.value      = value

  def __str__(self):
    return 'Token(type="{type}", value="{val}")'.format(
      type = self.type,
      val  = self.value
    )
    
  def __repr__(self):
    return self.__str__()
    
    
class Lexer (object):
  def __init__(self, text, config):
    self.text     = text
    self.config   = config
    self.lineInd  = 0
    self.charInd  = 0
    self.complete = False
    
    #Get token and keyword list
    self.tokens   = self.config['tokens']
    self.keywords = self.config['keywords']
    
    #Split lines
    self.text = text.split('\n')
    print(text)
    
    self.numLines = len(self.text)
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
      
    if len(self.text) == self.lineInd:
      self.complete = True
      
      
  def matchKeywords(self, matchStr):
    for keyword in self.keywords:
      if matchStr == keyword['regex']:
        return keyword['regex']
    return None
    
  def get_next_token(self):
    #Return EOF if lexer reached end of text
    if self.complete:
      return Token('EOF',None)
    
    #Get Str
    lineStr = self.text[self.lineInd][self.charInd:]
    
    #Remove whitespace first
    matchObj = re.match('\s+',lineStr)
    if matchObj:
      self.advanceIndex(matchObj.group(0))
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
          if keyword is not None:
            token = Token(keyword, matchStr)
          else:
            token = Token(token['type'], matchStr)
        else:
          token = Token(token['type'], matchStr)
        self.advanceIndex(matchStr)
        return token
    
    raise Exception('Invalid character "{0}"'.format(re.match('(\S*)',lineStr).group(0)))
    
    
def main():
  #Load Lexer Configuration
  lexerConfig = yaml.load(lexerConfigStr)
  
  #First Test String
  #testStr = 'x = y and 1'
  #testStr = 'x = y and 1\n  y = z or 0'
  testStr = 'spro(clk,rst):\n  x = y and 8'
  
  lexer = Lexer(testStr, lexerConfig)
  token = lexer.get_next_token()
  print('Found! {0}'.format(token))
  while (token.type != 'EOF'):
    token = lexer.get_next_token()
    print('Found! {0}'.format(token))
    
    
if __name__ == '__main__':
  main()
