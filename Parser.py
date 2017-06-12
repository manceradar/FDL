from Lexer import Lexer
from Lexer import Token
import re

#Create an abstract class for abstract-syntax tree (AST)
class BaseAST:
  def __init__(self, scope, base, grammerDict):
    #Scope this node is in
    self.scope  = scope
    
    #Base name
    self.base   = base
    
    #Add variables based on dict values
    for var, val in grammerDict.iteritems():
      setattr(self, var, val)
            
  def __str__(self):
    return str(self.__dict__)


class Parser:
  def __init__(self, lexer):
    self.lexer = lexer
    self.token = self.lexer.get_next_token()
    self.skip()
  
  def error(self, expectedTokenType):
    print('Unexpected syntax: Line #{0}\nExpected {1} but got {2}, value="{3}"'.format(self.token.lineNo, expectedTokenType, self.token.type, self.token.value))
    raise Exception('Unexpected syntax')
  
  # Read next token, but skipping comments
  def next(self):
    #Get next token, skipping over comments
    self.token = self.lexer.get_next_token()
    if (self.check('COMMENT')):
      self.token = self.lexer.get_next_token()
      
  # Read next token, but skipping comments and EOL
  def skip(self):
    #Get next token, skipping over comments
    while (self.check(['COMMENT', 'EOL'])):
      self.token = self.lexer.get_next_token()
    
  # can check str or list of str
  def check(self, expectedTokenType):
    if (type(expectedTokenType) is str):
      return (self.token.type == expectedTokenType)
    elif (type(expectedTokenType) is list):
      return (self.token.type in expectedTokenType)
    
  def verify(self, expectedTokenType):
    if (type(expectedTokenType) is str):
      if (self.check(expectedTokenType)):
        self.next()
      else:
        self.error(expectedTokenType)
    elif (type(expectedTokenType) is list):
      if (self.token.type in expectedTokenType):
        self.next()
      else:
        self.error(expectedTokenType)
    else:
      raise Exception('Verify type "{0}" not valid'.format(type(expectedTokenType)))
      
  def getScope(self):
    return self.token.scope
    
  def getValue(self):
    return self.token.value
  
  def getType(self):
    return self.token.type
    
  def parse(self):
    # Create dict
    fileDict = dict()
   
    # Check for import
    importNodes = self.loadLibrary()
    fileDict['importNodes'] = importNodes
    
    # Check for module
    if (self.check('MODULE')):
      moduleNode = self.loadModule()
    else:
      moduleNode = None
      
    fileDict['moduleNode'] = moduleNode
    
    # Create Root Node
    return BaseAST(None, 'FILE', fileDict)
    
  def loadLibrary(self):
    importNodes = []
    
    # Load line (IMPORT ID (DOT ID)? EOL)*
    while (self.check('IMPORT')):
      # Get scope
      scope = self.getScope()
      
      # Create library dict
      libDict = dict()
      base = self.getType()
      self.verify('IMPORT')
      libDict['library'] = self.getValue()
      self.verify('ID')
        
      # Check if DOT is used to only load one item
      if (self.check('DOT')):
        self.verify('DOT')
        libDict['load'] = self.getValue()
        self.verify('ID')
      else:
        libDict['load'] = 'all'
      
      # Skip
      self.skip()
      
      # Create node
      importNodes.append(BaseAST(scope, base, libDict))
          
    # No import line, move on
    return importNodes
    
  def loadModule(self):
    # Read module line (MODULE ID COLON)
    modScope = self.getScope()
    base = self.getType()
    self.verify('MODULE')
    modDict = dict()
    modDict['name'] = self.getValue()
    self.verify('ID')
    self.verify('COLON')
    self.skip()
    
    # Check for generic declarations
    if (self.check('GENERICS')):
      genDeclNodes = self.loadGenerics()
    else:
      genDeclNodes = []
    modDict['genDeclNodes'] = genDeclNodes
    
    # Load interface declarations
    modDict['portDeclNodes'] = self.loadPorts()
    
    # Load architecture
    modDict['archNode'] = self.loadArch()
    
    #Create module node
    return BaseAST(modScope, base, modDict)
    
  def loadGenerics(self):
    # Load line (GENERICS COLON EOL)
    genScope = self.token.type
    self.verify('GENERICS')
    self.verify('COLON')
    self.verify('EOL')
    self.skip()
    
    # Loop over all generic variables
    genVars = []
    while (self.check('ID')):
      # Create variable declaration
      genVars.append(self.loadVarDecl('gen'))
      
    # No more generics
    return genVars
    
  def loadPorts(self):
    # Load line (PORTS COLON EOL)
    genScope = self.token.type
    self.verify('PORTS')
    self.verify('COLON')
    self.verify('EOL')
    self.skip()
    
    # Loop over all ports
    portVars = []
    while (self.check('ID')):
      # Create port declaration
      portVars.append(self.loadVarDecl('port'))
      
    return portVars
    
  def loadArch(self):
    # Get arch scope
    # Load line (ARCH ID COLON)
    archScope = self.getScope()
    base = self.getType()
    self.verify('ARCHBLOCK')
    archDict = {'name': self.getValue()}
    self.verify('ID')
    self.verify('COLON')
    self.skip()
    
    #Next load signal definitions
    #Load line (SIGNALS COLON)
    archDict['signalScope'] = self.getScope()
    self.verify('SIGNALBLOCK')
    self.verify('COLON')
    self.skip()
    
    # Loop over all signal declarations
    sigVars =[]
    while (self.check('ID')):
      # Create signal declaration
      sigVars.append(self.loadVarDecl('var'))
      
    archDict['sigDeclNodes'] = sigVars
    
    #Next load logic
    #Load line (LOGIC COLON)
    archDict['logicScope'] = self.getScope()
    self.verify('LOGICBLOCK')
    self.verify('COLON')
    self.skip()
    archDict['statements'] = self.loadStatementList()
    
    return BaseAST(archScope, base, archDict)
    
  def loadVarDecl(self, declType):
    # Load line for gen  (TYPE (ARG_LIST)? (INDEX_LIST)* ID (ASSIGN EXPR)?)
    # Load line for port (TYPE (ARG_LIST)? (INDEX_LIST)* INTERFACE_TYPE ID)
    # Load line for var  ((CONST)? TYPE (ARG_LIST)? (INDEX_LIST)* ID (ASSIGN EXPR)?)
    varScope = self.getScope()
    varType = dict()
    
    if (declType is 'var'):
      if (self.check('CONST')):
        varType['const'] = True
      else:
        varType['const'] = False
    elif (declType is 'gen'):
      varType['const'] = True
    else:
      varType['const'] = False
    
    
    # Define variable
    varType['type'] = self.getValue()
    self.verify('ID')
    
    # Determine type def
    if (self.check('LPAREN')):
      varType['typeConfig'] = self.loadArgList(True)
    else:
      varType['typeConfig'] = []
      
    # Determine array size
    varType['decl'] = True
    if (self.check('LBRACK')):
      varType['array'] = self.loadIndexList(True)
    else:
      varType['array'] = [[0,0]]
      
    # Only ports have interface types
    if (declType is 'port'):
      # Interface type
      varType['port'] = self.getValue()
      self.verify('INTERFACE_TYPE')
    else:
      varType['port'] = None
    
    # Name
    varType['name'] = self.getValue()
    self.verify('ID')
    
    # Only variables and gen can have initial values
    if (declType is not 'port'):
      #Check for initial value
      if (self.check('ASSIGN')):
        self.verify('ASSIGN')
        varType['value'] = self.loadExpr(True)
      else:
        varType['value'] = [None]
    else:
      varType['value'] = [None]
    
    # Verify no more syntax this line
    self.verify('EOL')
    
    # Skip
    self.skip()
    
    return BaseAST(varScope, 'DECL', varType)
    
  def loadStatementList(self):
    # Load statements (ASSIGNMENT | SYNCPRO | ASYNCPRO | PROCESS)
    checkList = ['ID', 'SYNCPRO', 'ASYNCPRO', 'PROCESS']
    statementNodes = []
    while (self.check(checkList)):
      statementNodes.append(self.loadStatement())
    
    return statementNodes
    
  def loadStatement(self):
    # TODO: check others
    if (self.check('SYNCPRO')):
      return self.loadSpro()
    elif (self.check('ID')):
      return self.loadAssignment()
      
  def loadAssignment(self):
    # Load line (VAR ASSIGN EXPR)
    asgnScope = self.getScope()
    asgnDict = dict()
    asgnDict['leftVar'] = self.loadVar(False)
    self.verify('ASSIGN')
    asgnDict['rightExpr'] = self.loadExpr(False)
    self.skip()
    return BaseAST(asgnScope, 'ASSIGNMENT', asgnDict)
      
  def loadSpro(self):
    # Load line (SYNCPRO ARG_LIST COLON)
    sproScope = self.getScope()
    base = self.getType()
    self.verify('SYNCPRO')
    sproDict = {'args': self.loadArgList(True)}
    self.verify('COLON')
    self.next()
    
    # Load (ASSIGNMENT)
    statementNodes = []
    while (self.check('ID')):
      statementNodes.append(self.loadStatement())
      
    sproDict['statements'] = statementNodes
    
    return BaseAST(sproScope, base, sproDict)
    
  # isDecl specifies if this is a declaration call or assignment call
  # this variable will be passed to syntax checker to verify
  # array sizes are constant values. assignment array sizes can be 
  # constant or signal
  def loadExpr(self,isDecl):
    # Load (TERM (ADD_SUB TERM)*)
    exprDict = dict()
    exprDict['left'] = self.loadTerm(isDecl)
    
    while (self.check(['ADD_SUB','CAT'])):
      exprDict['op'] = self.getValue()
      self.verify(['ADD_SUB','CAT'])
      exprDict['right'] = self.loadTerm(isDecl)
      
    return BaseAST(None, 'EXPR', exprDict)
    
  def loadTerm(self, isDecl):
    # Load (FACTOR (MUL_DIV FACTOR)*)
    termDict = dict()
    termDict['left'] = self.loadFactor(isDecl)
    
    while (self.check('MUL_DIV')):
      termDict['op'] = self.getValue()
      self.verify('MUL_DIV')
      termDict['right'] = self.loadFactor(isDecl)
      
    return BaseAST(None, 'TERM', termDict)
    
  def loadFactor(self, isDecl):
    # CONST = (INTEGER | FLOAT | BIT_INIT | STRING)
    # Load (((ADD_SUB | CAT) FACTOR) | CONST | (LPAREN EXPR RPAREN) | VAR)
    constList = ['INTEGER','FLOAT','BIT_INIT_HEX','BIT_INIT_BIN','STRING']
    operList = ['ADD_SUB']
    if (self.check(operList)):
      factDict = dict()
      base = self.getType()
      self.verify(operList)
      factDict['op']   = [self.getValue()]
      self.verify('ADD_SUB')
      factDict['expr'] = [self.loadFactor(isDecl)]
      return BaseAST(None, base, factDict)
    elif (self.check(constList)):
      numDict = dict()
      typeStr = self.getType()
      valStr = self.getValue()
      numDict['type']  = typeStr
      if (typeStr == 'INTEGER'):
        numDict['value'] = [int(valStr)]
      elif (typeStr == 'FLOAT'):
        numDict['value'] = [float(valStr)]
      elif (typeStr == 'BIT_INIT_BIN'):
        numDict['type'] = 'BIT_INIT'
        binData = re.match('[b]?\'([0-1]+)\'',valStr).group(1)
        numDict['value'] = binData
      elif (typeStr == 'BIT_INIT_HEX'):
        numDict['type'] = 'BIT_INIT'
        hexData = re.match('x\'([0-9a-fA-F]+)\'',valStr).group(1)
        binData = bin(int(hexData, 16))[2:].zfill(4*len(hexData))
        numDict['value'] = binData
      elif (typeStr == 'STRING'):
        numDict['value'] = valStr
      
      numDict['const'] = True
      numDict['array'] = [[0,0]]
      numDict['decl']  = isDecl
      self.verify(constList)
      return BaseAST(None, 'NUM', numDict)
    elif (self.check('LPAREN')):
      return self.loadExpr(isDecl)
    else:
      return self.loadVar(isDecl)
    
  def loadVar(self, isDecl):
    #Load (ID (INDEX_LIST)? (DOT ID (INDEX_LIST)?))
    varScope = self.getScope()
    varDict = dict()
    varDict['name'] = self.getValue()
    self.verify('ID')
    
    varDict['decl'] = isDecl
    
    # check slice
    if (self.check('LBRACK')):
      varDict['array'] = self.loadIndexList(isDecl)
    else:
      varDict['array'] = [None]
      
    # check for struct or interface variable
    if (self.check('DOT')):
      # TODO
      pass
    else:
      varDict['field'] = None
      
    return BaseAST(varScope, 'VAR', varDict)
    
  def loadArgList(self, isDecl):
    # Load line (LPAREN EXPR (COMMA EXPR)* RPAREN)
    self.verify('LPAREN')
    argNodes = [self.loadExpr(isDecl)]
    while (self.check('COMMA')):
      self.verify('COMMA')
      argNodes.append(self.loadExpr(isDecl))
      
    self.verify('RPAREN')
    return argNodes
    
  def loadIndexList(self, isDecl):
    # Load line (INDEX)*
    sliceList = []
    while (self.check('LBRACK')):
      sliceList.append(self.loadIndex(isDecl))
      
    return sliceList
    
  def loadIndex(self, isDecl):
    # Load line (LBRACK EXPR (COLON EXPR)? RBRACK)
    self.verify('LBRACK')
    left  = self.loadExpr(isDecl)
    # Slice
    if (self.check('COLON')):
      self.verify('COLON')
      right = self.loadExpr(isDecl)
      self.verify('RBRACK')
      
    # Index
    else:
      right = left
      self.verify('RBRACK')
      
    return [left, right]
    

