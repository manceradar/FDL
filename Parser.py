from Lexer import Lexer
from Lexer import Token

#Create an abstract class for abstract-syntax tree (AST)
class BaseAST(object):
  def __init__(self, scope, grammerDict):
    #Scope this node is in
    self.scope  = scope
    
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
    while (self.check('COMMENT') or self.check('EOL')):
      self.token = self.lexer.get_next_token()
    
  # can check str or list of str
  def check(self, expectedTokenType):
    if (type(expectedTokenType) is str):
      return (self.token.type == expectedTokenType)
    elif (type(expectedTokenType) is list):
      return (self.token.type in expectedTokenType)
    
  def verify(self, expectedTokenType):
    if (self.check(expectedTokenType)):
      self.next()
    else:
      self.error(expectedTokenType)
    
  def loadLibrary(self):
    importNodes = []
    
    # Loop over all potential import statements
    while (self.check('IMPORT')):
      # Get scope
      scope = self.token.scope
      
      # Create library dict
      libDict = dict()
      self.verify('IMPORT')
      libDict['name'] = self.token.value
      self.verify('ID')
        
      # Check if DOT is used to only load one item
      if (self.check('DOT')):
        self.verify('DOT')
        libDict['load'] = self.token.value
        self.verify('ID')
      else:
        libDict['load'] = 'all'
      
      # Check no other syntax this line
      self.verify('EOL')
      
      # Skip
      self.skip()
      
      # Create node
      importNodes.append(BaseAST(scope, libDict))
          
    # No import line, move on
    return importNodes
    
  def loadModule(self):
    # Read module line (MODULE ID COLON)
    modScope = self.token.scope
    self.verify('MODULE')
    modDict = dict()
    modDict['name'] = self.token.value
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
    return BaseAST(modScope, modDict)
    
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
      genVars.append(self.loadVarDecl(False))
      
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
      portVars.append(self.loadVarDecl(True))
      
    return portVars
    
  def loadArch(self):
    # Get arch scope
    # Load line (ARCH ID COLON)
    archScope = self.token.scope
    self.verify('ARCHBLOCK')
    archDict = {'name': self.token.value}
    self.verify('ID')
    self.verify('COLON')
    self.skip()
    
    #Next load signal definitions
    #Load line (SIGNALS COLON)
    archDict['signalScope'] = self.token.scope
    self.verify('SIGNALBLOCK')
    self.verify('COLON')
    self.skip()
    
    # Loop over all signal declarations
    sigVars =[]
    while (self.check('ID')):
      # Create signal declaration
      sigVars.append(self.loadVarDecl(False))
      
    archDict['sigDeclNodes'] = sigVars
    
    #Next load logic
    #Load line (LOGIC COLON)
    archDict['logicScope'] = self.token.scope
    self.verify('LOGICBLOCK')
    self.verify('COLON')
    self.skip()
    archDict['statements'] = self.loadStatementList()
    
    return BaseAST(archScope, archDict)
    
  def loadVarDecl(self, port):
    #                    TYPE
    #                     ||
    # Load line for var  (ID (ARG_LIST)? (SLICE_LIST)* ID (ASSIGN EXPR)?)
    # Load line for port (ID (ARG_LIST)? (SLICE_LIST)* INTERFACE_TYPE ID)
    varScope = self.token.scope
    
    # TODO: Lookup symbol
    
    # Define variable
    varType = dict()
    varType['type'] = self.token.value
    self.verify('ID')
    
    # Determine type def
    if (self.check('LPAREN')):
      varType['typeConfig'] = self.loadArgList()
    else:
      varType['typeConfig'] = None
      
    # Determine array size
    if (self.check('LBRACK')):
      varType['array'] = self.loadSliceList()
    else:
      varType['array'] = [[0, 0]]
      
    # Only ports have interface types
    if (port):
      # Interface type
      varType['port'] = self.token.value
      self.verify('INTERFACE_TYPE')
    
    # Name
    varType['name'] = self.token.value
    self.verify('ID')
    
    # Only variables can have initial values
    if (not port):
      #Check for initial value
      if (self.check('ASSIGN')):
        self.verify('ASSIGN')
        varType['init'] = self.loadArg()
      else:
        varType['init'] = None
    
    # Verify no more syntax this line
    self.verify('EOL')
    
    # Skip
    self.skip()
    
    return BaseAST(varScope,varType)
    
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
    asgnScope = self.token.scope
    asgnDict = dict()
    asgnDict['leftVar'] = self.loadVar()
    self.verify('ASSIGN')
    asgnDict['rightExpr'] = self.loadExpr()
    self.skip()
    return BaseAST(asgnScope,asgnDict)
      
  def loadSpro(self):
    # Load line (SYNCPRO ARG_LIST COLON)
    sproScope = self.token.scope
    self.verify('SYNCPRO')
    sproDict = {'args': self.loadArgList()}
    self.verify('COLON')
    self.next()
    
    # Load (ASSIGNMENT)
    statementNodes = []
    while (self.check('ID')):
      statementNodes.append(self.loadStatement())
      
    sproDict['statements'] = statementNodes
    
    return BaseAST(sproScope, sproDict)
    
  def loadVar(self):
    #Load (ID (SLICE_LIST)? (DOT ID (SLICE_LIST)?))
    varScope = self.token.scope
    varDict = dict()
    varDict['name'] = self.token.value
    self.verify('ID')
    
    # check slice
    if (self.check('LBRACK')):
      varDict['array'] = self.loadSliceList()
    else:
      varDict['array'] = [[0, 0]]
      
    # check for struct or interface variable
    if (self.check('DOT')):
      # TODO
      pass
    else:
      varDict['field'] = None
      
    return BaseAST(varScope, varDict)
    
  def loadExpr(self):
    # Load
    exprDict = dict()
    exprDict['left'] = self.loadVar()
    if (self.check('CAT')):
      exprDict['op'] = 'CAT'
      self.verify('CAT')
      exprDict['right'] = self.loadVar()
    else:
      exprDict['right'] = None
    return BaseAST(None,exprDict)
    
  def loadArgList(self):
    # Load line (LPAREN ARG (COMMA ARG)* RPAREN)
    self.verify('LPAREN')
    argNodes = [self.loadArg()]
    while (self.check('COMMA')):
      self.verify('COMMA')
      argNodes.append(self.loadArg())
      
    self.verify('RPAREN')
    return argNodes
    
  def loadArg(self):
    # ARG = (ID | INTEGER | FLOAT | BIT_INIT | STRING)
    argNode = {'value': self.token.value, 'type': self.token.type}
    if (self.check('ID')):
      self.verify('ID')
    elif (self.check('INTEGER')):
      self.verify('INTEGER')
    elif (self.check('FLOAT')):
      self.verify('FLOAT')
    elif (self.check('BIT_INIT')):
      self.verify('BIT_INIT')
    elif (self.check('STRING')):
      self.verify('STRING')
    else:
      self.error('ARG')
      
    return argNode
    
  def loadSliceList(self):
    # Load line (SLICE)*
    sliceList = []
    while (self.check('LBRACK')):
      sliceList.append(self.loadSlice())
      
    return sliceList
    
  def loadSlice(self):
    # Load line (LBRACK ARG COLON ARG RBRACK)
    self.verify('LBRACK')
    left  = self.loadArg()
    # Slice
    if (self.check('COLON')):
      self.verify('COLON')
      right = self.loadArg()
      self.verify('RBRACK')
      
    # Index
    else:
      right = None
      self.verify('RBRACK')
      
    return [left, right]
    
  def parse(self):
    # Create dict
    fileDict = dict()
   
    # Check for import (IMPORT ID (DOT ID)? EOL)*
    importNodes = self.loadLibrary()
    fileDict['importNodes'] = importNodes
    
    # Check for module
    if (self.check('MODULE')):
      moduleNode = self.loadModule()
    else:
      moduleNode = None
      
    fileDict['moduleNode'] = moduleNode
    
    # Create Root Node
    rootNode = BaseAST(None,fileDict)
        
    # Debug
    print('\nImport')
    for node in importNodes:
      print(node)
      
    print('\n')
    print('Module "{0}""'.format(moduleNode.name))
    print('Generics')
    for node in moduleNode.genDeclNodes:
      print(node)
    print('Ports')
    for node in moduleNode.portDeclNodes:
      print(node)
    archNode = moduleNode.archNode
    print('Architecture "{0}"'.format(archNode.name))
    print('Signal Scope {0}'.format(archNode.signalScope))
    for node in archNode.sigDeclNodes:
      print(node)
    print('Logic Scope {0}'.format(archNode.logicScope))
    for node in archNode.statements:
      print(node)
      for state in node.statements:
        print(state.leftVar)
        print(state.rightExpr.left)
        print(state.rightExpr.right)
