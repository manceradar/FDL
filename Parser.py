from Lexer import Lexer
from Lexer import Token
import re

#Simple class to keep track of code scope. FDL is
#scoped using tabs/spaces.
class SimpleScope(object):
  def __init__(self,baseScope):
    self.scope = [baseScope]
    
  def add(self, scope):
    # Verify scope is larger that current
    if (scope > self.get()):
      self.scope.append(scope)
      return True
    else:
      return False
    
  def rm(self):
    self.scope.pop()
  
  def get(self):
    return self.scope[-1]
    
  def report(self):
    print('Scope = {0}'.format(str(self.scope)))

#Create an abstract class for abstract-syntax tree (AST)
class BaseAST(object):
  def __init__(self, base, comments, grammerDict):
    #Base name
    self.base   = base
    
    #Comments included
    self.comments = comments
    
    #Add variables based on dict values
    for var, val in grammerDict.iteritems():
      setattr(self, var, val)
            
  def __str__(self):
    return str(self.__dict__)


class Parser(object):
  def __init__(self, lexer):
    self.lexer = lexer
    self.token = self.lexer.get()
    self.scope = None
    self.skip()
  
  def error(self, expectedTokenType=None):
    tType = self.getType()
    tVal = self.getValue()
    tScope = self.getScope()
    print('Unexpected syntax: Line #{0}'.format(self.token.lineNo))
    if (expectedTokenType is not None):
      print('Expected Token {0} but got {1}, value="{2}"'.format(expectedTokenType, tType, tVal))
    print('Expected Scope {0} but got {1}'.format(self.scope.get(), tScope))
    raise Exception('Unexpected syntax')
  
  # Read next token
  def next(self):
    #Get next token
    self.token = self.lexer.get()
    
  # Peek at next token
  def peek(self):
    return self.lexer.peek()
      
  # Read next token, but skipping comments and EOL
  def skip(self):
    #Comment list
    comment = []
    
    #Get next token, skipping over comments
    while (self.check(['COMMENT', 'EOL'])):
      #Add comment to list
      if (self.check('COMMENT')):
        comment.append(self.getValue())
        
      self.token = self.lexer.get()
      
    return comment
    
  # can check str or list of str
  def check(self, expectedTokenType, checkScope=False):
    if (type(expectedTokenType) is str):
      tokenGood = (self.token.type == expectedTokenType)
    elif (type(expectedTokenType) is list):
      tokenGood = (self.token.type in expectedTokenType)
    else:
      raise Exception('Parser: Check type "{0}" not valid'.format(type(expectedTokenType)))
      
    # Check if scope is good
    if checkScope:
      scopeGood = (self.getScope() == self.scope.get())
    else:
      scopeGood = True
      
    # Determine if scope and token are good
    return (tokenGood and scopeGood)
    
  def verify(self, expectedTokenType, checkScope=False):
    if (self.check(expectedTokenType,checkScope)):
      self.next()
    else:
      self.error(expectedTokenType)
      
  def getScope(self):
    return self.token.scope
    
  def getValue(self):
    return self.token.value
  
  def getType(self):
    return self.token.type
    
  def addScope(self):
    newScope = self.getScope()
    if (not self.scope.add(newScope)):
      self.error()
    
  def rmScope(self):
    self.scope.rm()
    
  def parse(self):
    # Create dict
    fileDict = dict()
    
    comment = self.skip()
    
    # Determine base scope
    self.scope = SimpleScope(self.getScope())
   
    # Check for import
    nodes = self.loadImport()
    
    # Check for module
    decl = ['MODULE','LIBRARY']
    while (self.check(decl,True)):
      if (self.getType() == 'MODULE'):
        nodes.append(self.loadModuleDecl())
      elif (self.getType() == 'LIBRARY'):
        nodes.append(self.loadLibraryDecl())
      
    fileDict['nodes']= nodes

    # Create Root Node
    return BaseAST('FILE', comment, fileDict)
    
  def loadImport(self):
    importNodes = []
    
    # Load line (IMPORT ID (DOT ID)?)*
    while (self.check('IMPORT',True)):
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
      comment = self.skip()
      
      # Create node
      importNodes.append(BaseAST(base, comment, libDict))
          
    # No import line, move on
    return importNodes
    
  def loadLibraryDecl(self):
    # Load line (LIBRARY ID COLON)
    base = self.getType()
    self.verify('LIBRARY',True)
    libDict = dict()
    libDict['name'] = self.getValue()
    self.verify('ID')
    self.verify('COLON')
    comment = self.skip()
    
    #Increase scope
    self.addScope()
    
    #Load definitions
    nodes = []
    decl = ['STRUCT','INTERFACE','DEF','ENUM','ID']
    while (self.check(decl,True)):
      if (self.check('STRUCT')):
        print('Load struct...')
        nodes.append(self.loadStruct())
      elif (self.check('INTERFACE')):
        print('Load interface...')
        nodes.append(self.loadInterface())
      elif (self.check('DEF')):
        print('Load function...')
        nodes.append(self.loadFunction())
      elif (self.check('ID')):
        print('Load variable...')
        nodes.append(self.loadVarDecl('var'))
      elif (self.check('ENUM')):
        print('Load enum...')
        nodes.append(self.loadEnumDecl())
        
    #Done and decrease scope
    self.rmScope()
    
    libDict['nodes'] = nodes
    
    return BaseAST(base, comment, libDict)
    
  def loadStruct(self):
    # Load line (STRUCT ID (DECL_ARG_LIST)? COLON)
    base = self.getType()
    self.verify('STRUCT')
    structDict = dict()
    structDict['name'] = self.getValue()
    self.verify('ID')
    
    #See if configuration parameters exist
    if (self.check('LPAREN')):
      structDict['config'] = self.loadDeclArgList()
    else:
      structDict['config'] = []
      
    self.verify('COLON')
    comment = self.skip()
    
    self.addScope()
    
    #Load fields
    nodes = []
    while (self.check('ID',True)):
      #Load Field
      nodes.append(self.loadStructField())
      
    #Return to original scope
    self.rmScope()
      
    #Return field node
    structDict['fieldNodes'] = nodes
    return BaseAST(base, comment, structDict)
    
  def loadStructField(self):
    # Load line (TYPE (CALL_ARG_LIST)? (INDEX_LIST)? ID)
    varType = dict()
    
    # Define variable
    varType['type'] = self.getValue()
    self.verify('ID')
    
    # Determine type def
    if (self.check('LPAREN')):
      varType['typeConfig'] = self.loadCallArgList(True)
    else:
      varType['typeConfig'] = []
      
    # Determine array size
    varType['decl'] = True
    if (self.check('LBRACK')):
      varType['array'] = self.loadIndexList(True)
    else:
      varType['array'] = [[0,0]]
    
    # Name
    varType['name'] = self.getValue()
    self.verify('ID')
    
    # Skip
    comment = self.skip()
    
    return BaseAST('FIELD', comment, varType)
    
  def loadInterface(self):
    # Load line (INTERFACE ID (DECL_ARG_LIST)? COLON)
    base = self.getType()
    self.verify('INTERFACE')
    itfcDict = dict()
    itfcDict['name'] = self.getValue()
    self.verify('ID')
    
    #See if configuration parameters exist
    if (self.check('LPAREN',True)):
      itfcDict['config'] = self.loadDeclArgList()
    else:
      itfcDict['config'] = []
      
    self.verify('COLON')
    comment = self.skip()
    
    self.addScope()
    
    #Load fields
    nodes = []
    while (self.check('ID',True)):
      #Load Field
      nodes.append(self.loadInterfaceField())
      
    #Return to original scope
    self.rmScope()
      
    #Return field node
    itfcDict['fieldNodes'] = nodes
    return BaseAST(base, comment, itfcDict)
    
  def loadInterfaceField(self):
    # Load line (TYPE (CALL_ARG_LIST)? (INDEX_LIST)? BASE_INTERFACE ID)
    varType = dict()
    
    # Define variable
    varType['type'] = self.getValue()
    self.verify('ID')
    
    # Determine type def
    if (self.check('LPAREN')):
      varType['typeConfig'] = self.loadCallArgList(True)
    else:
      varType['typeConfig'] = []
      
    # Determine array size
    varType['decl'] = True
    if (self.check('LBRACK')):
      varType['array'] = self.loadIndexList(True)
    else:
      varType['array'] = [[0,0]]
      
    #Master interface direction
    varType['port'] = self.getValue()
    self.verify('BASE_INTERFACE')
    
    # Name
    varType['name'] = self.getValue()
    self.verify('ID')
    
    # Skip
    comment = self.skip()
    
    return BaseAST('FIELD', comment, varType)
    
  def loadFunction(self):
    # Load line (DEF ID DECL_ARG_LIST COLON)
    base = 'FUNCTION'
    self.verify('DEF',True)
    funcDict = dict()
    funcDict['name'] = self.getValue()
    functionNames = ['ID', 'LOGICAL_OPER', 'SHIFT_OPER', 'MOD_REM_OPER', 'NOT_OPER']
    self.verify(functionNames)
    
    #Load function arguments
    funcDict['config'] = self.loadDeclArgList()
      
    self.verify('COLON')
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    #Load function statements
    nodes = self.loadFuncStatements()
      
    #Return to original scope
    self.rmScope()
      
    #Return field node
    funcDict['nodes'] = nodes
    return BaseAST(base, comment, funcDict)
    
  def loadCallArgList(self, isDecl):
    # Load line (LPAREN SIMP_EXPR (COMMA SIMP_EXPR)* RPAREN)
    self.verify('LPAREN')
    argNodes = [self.loadSimpleExpr(isDecl)]
    while (self.check('COMMA')):
      self.verify('COMMA')
      argNodes.append(self.loadSimpleExpr(isDecl))
      
    self.verify('RPAREN')
    return argNodes
    
  def loadDeclArgList(self):
    # Load line (LPAREN DECL_ARG (COMMA DECL_ARG)* RPAREN)
    self.verify('LPAREN')
    argNodes = [self.loadDeclArg()]
    while (self.check('COMMA')):
      self.verify('COMMA')
      argNodes.append(self.loadDeclArg())
      
    self.verify('RPAREN')
    return argNodes
    
  def loadDeclArg(self):
    #Load line (TYPE (STAR)* ID)
    # Define variable
    varType = dict()
    varType['type'] = self.getValue()
    self.verify('ID')
    
    #Determine number of dimensions
    dim = 1
    while (self.check('STAR')):
      dim += 1
      self.verify('STAR')
      
    varType['dim'] = dim
    
    #Get name
    varType['name'] = self.getValue()
    self.verify('ID')
    
    return BaseAST('ARG', [], varType)
      
  def loadModuleDecl(self):
    # Read module line (MODULE ID COLON)
    base = self.getType()
    self.verify('MODULE', True)
    modDict = dict()
    modDict['name'] = self.getValue()
    self.verify('ID')
    self.verify('COLON')
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    # Check for generic declarations
    genDeclNodes = []
    if (self.check('GENERICS')):
      genDeclNodes.append(self.loadGenericDecl())
      
    modDict['genDeclNodes'] = genDeclNodes
    
    # Load interface declarations
    modDict['portDeclNodes'] = self.loadPortDecl()
    
    #Return to original scope
    self.rmScope()
    
    # Load architecture
    modDict['archNode'] = self.loadArch()
    
    #Create module node
    return BaseAST(base, comment, modDict)
    
  def loadGenericDecl(self):
    # Load line (GENERICS COLON)
    self.verify('GENERICS',True)
    self.verify('COLON')
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    # Loop over all generic variables
    genVars = []
    while (self.check('ID')):
      # Create variable declaration
      genVars.append(self.loadVarDecl('gen'))
      
    #Return to original scope
    self.rmScope()
      
    # No more generics
    return genVars
    
  def loadPortDecl(self):
    # Load line (PORTS COLON)
    self.verify('PORTS',True)
    self.verify('COLON')
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    # Loop over all ports
    portVars = []
    while (self.check('ID')):
      # Create port declaration
      portVars.append(self.loadVarDecl('port'))
      
    #Return to original scope
    self.rmScope()
      
    return portVars
    
  def loadArch(self):
    # Get arch scope
    # Load line (ARCH ID COLON)
    base = self.getType()
    self.verify('ARCH', True)
    archDict = dict()
    archDict['module'] = self.getValue()
    self.verify('ID')
    self.verify('LPAREN')
    archDict['name'] = self.getValue()
    self.verify('ID')
    self.verify('RPAREN')
    self.verify('COLON')
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    # Check if signal block exists
    archDict['declareNode'] = None
    if (self.check('DECLARE')):
      #Next load signal definitions
      archDict['declareNode'] = self.loadDeclareBlock()
    
    #Next load logic
    archDict['logicBlock'] = self.loadLogicBlock()
    
    #Return to original scope
    self.rmScope()
    
    return BaseAST(base, comment, archDict)
    
  def loadDeclareBlock(self):
    #Load line (DECLARE COLON)
    base = self.getType()
    self.verify('DECLARE',True)
    self.verify('COLON')
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    # Loop over all declarations
    declNodes =[]
    decl = ['STRUCT','INTERFACE','DEF','ENUM','ID']
    while (self.check(decl,True)):
      if (self.check('STRUCT')):
        declNodes.append(self.loadStruct())
      elif (self.check('INTERFACE')):
        declNodes.append(self.loadInterface())
      elif (self.check('DEF')):
        declNodes.append(self.loadFunction())
      elif (self.check('ID')):
        declNodes.append(self.loadVarDecl('var'))
      elif (self.check('ENUM')):
        declNodes.append(self.loadEnumDecl())
      
    declDict = {'declNodes': declNodes}
    
    #Return to original scope
    self.rmScope()
    
    return BaseAST(base, comment, declDict)
    
  def loadLogicBlock(self):
    #Load line (LOGIC COLON)
    base = self.getType()
    self.verify('LOGIC',True)
    self.verify('COLON')
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    # Load logic statements
    logicDict = {'statements': self.loadLogicStatements()}
    
    #Return to original scope
    self.rmScope()
    
    return BaseAST(base, comment, logicDict)
    
  def loadVarDecl(self, declType):
    # Load line for gen  (TYPE (CALL_ARG_LIST)? (INDEX_LIST)? ID (ASSIGN CMPX_EXPR)?)
    # Load line for port (TYPE (CALL_ARG_LIST)? (INDEX_LIST)? INTERFACE_TYPE ID)
    # Load line for var  ((CONST)? TYPE (CALL_ARG_LIST)? (INDEX_LIST)? ID (ASSIGN CMPX_EXPR)?)
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
    self.verify('ID',True)
    
    # Determine type def
    if (self.check('LPAREN')):
      varType['typeConfig'] = self.loadCallArgList(True)
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
      self.verify(['BASE_INTERFACE','EXT_INTERFACE'])
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
        varType['value'] = self.loadComplexExpr(True)
      else:
        varType['value'] = [None]
    else:
      varType['value'] = [None]

    # Skip
    comment = self.skip()
    
    return BaseAST('DECL', comment, varType)
    
  def loadEnumDecl(self):
    # Load (ENUM ID ASSIGN LPAREN ID (COMMA ID)* RPAREN)
    base = self.getType()
    self.verify('ENUM')
    enumDict = dict()
    enumDict['var'] = self.getValue()
    self.verify('ID')
    self.verify('ASSIGN')
    self.verify('LPAREN')
    
    # Load states
    states = [self.getValue()]
    self.verify('ID')
    while (self.check('COMMA')):
      self.verify('COMMA')
      states.append(self.getValue())
      self.verify('ID')
      
    self.verify('RPAREN')
    enumDict['states'] = states
    comment = self.skip()
    
    return BaseAST(base,comment,enumDict)
    
  def loadLogicStatements(self):
    # Load logic statements
    # (ASSIGNMENT|FOR|CASE|IF|MODULE_INST|SPRO|APRO|PRO)
    statementNodes = []
    tokenList = ['ID', 'FOR', 'IF', 'CASE', 'SPRO', 'APRO', 'PRO']
    while (self.check(tokenList,True)):
      # Load all statements
      statementNodes.append(self.loadStatement(False))
    
    return statementNodes
    
  def loadFuncStatements(self):
    # Load function statements
    # (ASSIGNMENT|FOR|CASE|IF|MODULE_INST|RETURN)
    statementNodes = []
    tokenList = ['ID', 'FOR', 'IF', 'CASE', 'RETURN']
    while (self.check(tokenList,True)):
      statementNodes.append(self.loadStatement(False))
    
    return statementNodes
    
  def loadProStatements(self):
    # Load process statements
    # (ASSIGNMENT|FOR|CASE|IF)
    statementNodes = []
    tokenList = ['ID', 'FOR', 'IF', 'CASE']
    while (self.check(tokenList,True)):
      # Ensure not to load module inst.
      matchTuple = (self.getType(), self.peek().type)
      if (matchTuple == ('ID','ID')):
        #Module inst, error
        raise('Module instatiation detected in process')
      else:
        statementNodes.append(self.loadStatement(True))
    
    return statementNodes
    
  def loadStatement(self,isPro):
    # Allowed statements:
    
    if (self.check('SPRO')):
      return self.loadSpro()
    elif (self.check('APRO')):
      return self.loadApro()
    elif (self.check('PRO')):
      return self.loadPro()
    elif (self.check('FOR')):
      return self.loadFor()
    elif (self.check('IF')):
      return self.loadIf()
    elif (self.check('CASE')):
      pass
    elif (self.check('RETURN')):
      return self.loadReturn()
    elif (self.check('ID')):
      if (self.peek().type == 'ID'):
        return self.loadModuleInst()
      else:
        return self.loadAssignment()
    else:
      print('Type {0} not parsed.'.format(self.getType()))
      self.error()
      
  def loadSpro(self):
    # Load line (SPRO ARG_LIST COLON)
    base = self.getType()
    self.verify('SPRO')
    sproDict = {'args': self.loadCallArgList(True)}
    self.verify('COLON')
    comment = self.skip()
    
    # Load process statements
    sproDict['statements'] = self.loadProStatements()
    
    return BaseAST(base, comment, sproDict)
    
  def loadApro(self):
    # Load line (APRO ARG_LIST COLON)
    base = self.getType()
    self.verify('APRO')
    aproDict = {'args': self.loadCallArgList(True)}
    self.verify('COLON')
    comment = self.skip()
    
    # Load process statements
    aproDict['statements'] = self.loadProStatements()
    
    return BaseAST(base, comment, aproDict)
    
  def loadPro(self):
    # Load line (PRO ARG_LIST COLON)
    base = self.getType()
    self.verify('PRO')
    proDict = {'args': self.loadCallArgList(True)}
    self.verify('COLON')
    comment = self.skip()
    
    # Load process statements
    proDict['statements'] = self.loadProStatements()
    
    return BaseAST(base, comment, proDict)
    
  def loadFor(self,isPro):
    # Load line (FOR ID IN (RANGE_EXPR|VAR) COLON)
    base = self.getType()
    self.verify('FOR')
    forDict = dict()
    forDict['ind'] = self.getValue()
    self.verify('ID')
    self.verify('IN')
    if (self.check('RANGE')):
      #Load range expression
      forDict['iter'] = self.loadRangeExpr()
    else:
      forDict['iter'] = self.loadVar()
    
    self.verify('COLON')
    comment = self.skip()
    
    self.addScope()
    
    # Load process statements
    if (isPro):
      forDict['statements'] = self.loadProStatements()
    else:
      forDict['statements'] = self.loadLogicStatements()
      
    self.rmScope()
    
    return BaseAST(base, comment, forDict)
    
  def loadRangeExpr(self):
    # Load (RANGE LPAREN SIMP_EXPR COMMA SIMP_EXPR (COMMA SIMP_EXPR)? RPAREN)
    base = self.getType()
    rangeDict = dict()
    self.verify('RANGE')
    self.verify('LPAREN')
    rangeDict['left'] = self.loadSimpleExpr()
    self.verify('COMMA')
    rangeDict['right'] = self.loadSimpleExpr()
    if (self.check('COMMA')):
      self.verify('COMMA')
      rangeDict['stride'] = self.loadSimpleExpr()
    else:
      rangeDict['stride'] = 1
      
    self.verify('RPAREN')
    return BaseAST(base, [], rangeDict)
    
  def loadIf(self,isPro):
    # Load line (IF LPAREN SIMP_EXPR RPAREN COLON)
    base = self.getType()
    self.verify('IF')
    self.verify('LPAREN')
    ifDict = {'arg': self.loadSimpleExpr(False)}
    self.verify('RPAREN')
    self.verify('COLON')
    comment = self.skip()
    
    self.addScope()
    
    # Load statements
    if (isPro):
      # Load process
      ifDict['statements'] = self.loadProStatements()
    else:
      # Load logic
      ifDict['statements'] = self.loadLogicStatements()
      
    self.rmScope()
    
    # Check for ELIF
    ifDict['elif'] = []
    while (self.check('ELIF')):
      # Load elif
      ifDict['elif'].append(self.loadElif(isPro))
      
    # Check for ELSE
    ifDict['else'] = []
    if (self.check('ELSE')):
      ifDict['else'].append(self.loadElse(isPro))
    
    return BaseAST(base, comment, ifDict)
    
  def loadElif(self,isPro):
    # Load line (ELIF LPAREN SIMP_EXPR RPAREN COLON)
    base = self.getType()
    self.verify('ELIF')
    self.verify('LPAREN')
    elifDict = {'arg': self.loadSimpleExpr(False)}
    self.verify('RPAREN')
    self.verify('COLON')
    comment = self.skip()
    
    self.addScope()
    
    # Load statements
    if (isPro):
      # Load process
      elifDict['statements'] = self.loadProStatements()
    else:
      # Load logic
      elifDict['statements'] = self.loadLogicStatements()
      
    self.rmScope()
    
    return BaseAST(base, comment, ifDict)
    
  def loadElse(self,isPro):
    # Load line (ELSE COLON)
    base = self.getType()
    self.verify('ELSE')
    self.verify('COLON')
    comment = self.skip()
    
    self.addScope()
    
    # Load statements
    if (isPro):
      # Load process
      elseDict = {'statements': self.loadProStatements()}
    else:
      # Load logic
      elseDict = {'statements': self.loadLogicStatements()}
      
    self.rmScope()
    
    return BaseAST(base, comment, elseDict)
    
  def loadCase(self,isPro):
    # Load line (CASE LPAREN SIMP_EXPR RPAREN COLON)
    base = self.getType()
    self.verify('CASE')
    self.verify('LPAREN')
    caseDict = {'arg': self.loadSimpleExpr(False)}
    self.verify('RPAREN')
    comment = self.verify('COLON')
    
    self.addScope()
    
    # Load statements
    if (isPro):
      # Load process
      caseDict = {'statements': self.loadProStatements()}
    else:
      # Load logic
      caseDict = {'statements': self.loadLogicStatements()}
      
    self.rmScope()
    
    return BaseAST(base, comment, caseDict)
    
  def loadCaseChoice(self,isPro):
    # Load line (CHOICE COLON)
    caseDict = dict()
    case['choice'] = self.loadChoice(False)
      
  def loadAssignment(self):
    # Load line (VAR OPER CMPX_EXPR)
    # OPER = (ASSIGN|CMPD_ARITH_ASSIGN|CMPD_LOGICAL_ASSIGN|POST_OPER)
    asgnDict = dict()
    asgnDict['leftVar'] = self.loadVar(False)
    asgnList = ['ASSIGN', 'CMPD_ARITH_ASSIGN', 'CMPD_LOGICAL_ASSIGN', 'POST_OPER']
    asgnDict['op'] = self.getValue()
    operType = self.getType()
    self.verify(asgnList)
    
    # See if POST_OPER
    if (operType != 'POST_OPER'):
      asgnDict['rightExpr'] = self.loadComplexExpr(False)
      
    comment = self.skip()
    return BaseAST('ASSIGN', comment, asgnDict)
    
  def loadModuleInst(self):
    # Load line (ID ID (LPAREN ID RPAREN)? COLON)
    base = 'MODULE_INST'
    modDict = dict()
    modDict['name'] = self.getValue()
    self.verify('ID')
    modDict['module'] = self.getValue()
    self.verify('ID')
    
    # Determine if specific architecture is called
    if (self.check('LPAREN')):
      self.verify('LPAREN')
      modDict['arch'] = self.getValue()
      self.verify('ID')
      self.verify('RPAREN')
    else:
      modDict['arch'] = None
      
    self.verify('COLON')
    comment = self.skip()
    
    self.addScope()
    
    # Check for generic
    if (self.check('GENERICS')):
      modDict['gen'] = self.loadGenericInst()
      
    modDict['ports'] = self.loadPortInst()
    
    self.rmScope()
    
    return BaseAST(base,comment,modDict)
    
  def loadGenericInst(self):
    # Load line (GENERICS COLON)
    self.verify('GENERICS',True)
    self.verify('COLON')
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    # Loop over all generic variables
    genVars = []
    while (self.check('ID')):
      # Create variable declaration
      genVars.append(self.loadVarInst())
      
    #Return to original scope
    self.rmScope()
      
    # No more generics
    return genVars
    
  def loadPortInst(self):
    # Load line (PORTS COLON)
    self.verify('PORTS',True)
    self.verify('COLON')
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    # Loop over all ports
    portVars = []
    while (self.check('ID')):
      # Create port declaration
      portVars.append(self.loadVarInst())
      
    #Return to original scope
    self.rmScope()
      
    return portVars
    
  def loadVarInst(self):
    # Load line (VAR ASSIGN CMPX_EXPR)
    varDict = dict()
    varDict['port'] = self.loadVar(False)
    self.verify('ASSIGN')
    varDict['var'] = self.loadComplexExpr(False)
      
    comment = self.skip()
    return BaseAST('ASSIGN', comment, varDict)
    
  def loadReturn(self):
    # Load line (RETURN (VAR|(LPAREN VAR (COMMA VAR)* RPAREN)))
    self.verify('RETURN',True)
    vars = []
    if (self.check('LPAREN')):
      self.verify('LPAREN')
      vars.append(self.loadVar(False))
      
      while (self.check('COMMA')):
        vars.append(self.loadVar(False))
        
      self.verify('RPAREN')
      
    else:
      vars.append(self.loadVar(False))
      
    returnDict = {'vars': vars}
    comment = self.skip()
    
    return BaseAST('RETURN', comment, returnDict)
    
  # isDecl specifies if this is a declaration call or assignment call
  # this variable will be passed to syntax checker to verify
  # array sizes are constant values. assignment array sizes can be 
  # constant or signal
  def loadComplexExpr(self,isDecl):
    # Load (AGGREGATE | SIMP_EXPR)
    if (self.check('LBRACK')):
      return self.loadAggregate(isDecl)
    else:
      return self.loadSimpleExpr(isDecl)
    
  def loadAggregate(self,isDecl):
    # Load line (LBRACK ELEM_ASSOC (COMMA ELEM_ASSOC)* RBRACK)
    self.verify('LBRACK')
    args = [self.loadElemAssoc()]
    while (self.check('COMMA')):
      self.verify('COMMA')
      args.append(self.loadElemAssoc())
      
    self.verify('RBRACK')
    
    aggDict = {'nodes': args}
    
    return BaseAST('AGGREGATE', [], aggDict)
    
  def loadElemAssoc(self,isDecl):
    # Load (CHOICE ASSIGN (AGGREGATE|SIMP_EXPR))
    elemDict = dict()
    elemDict['left'] = self.loadChoice(isDecl)
    elemDict['op'] = self.getType()
    self.verify('ASSIGN')
    
    if (self.check('LBRACK')):
      elemDict['right'] = self.loadAggregate()
    else:
      elemDict['right'] = self.loadSimpleExpr()
    
    return BaseAST('ELEM', [], elemDict)
  
  def loadChoice(self,isDecl):
    # Load (SLICE|ID|OTHERS)
    if (self.check('OTHERS')):
      arg = self.getType()
      self.verify('OTHERS')
    else:
      tokenType = self.peek().type
      if (tokenType == 'ASSIGN'):
        #Parse a field assignment
        arg = self.getValue()
      else:
        #Parse a index
        arg = self.loadIndex()
        
    return arg
    
  def loadSimpleExpr(self,isDecl):
    # Load (RELATION (LOGICAL_OPER RELATION)*)
    exprDict = dict()
    node = self.loadRelation(isDecl)
    
    oper = ['LOGICAL_OPER']
    while (self.check(oper)):
      # Create new expr node
      exprDict['left'] = node
      exprDict['op']   = self.getType()
      self.verify(oper)
      exprDict['right'] = self.loadRelation(isDecl)
      node = BaseAST('EXPR', [], exprDict)
      
    return node
  
  def loadRelation(self,isDecl):
    # Load (SHIFT (RELATION_OPER SHIFT)*)
    exprDict = dict()
    node = self.loadShift(isDecl)
    
    oper = ['RELATION_OPER']
    while (self.check(oper)):
      # Create new expr node
      exprDict['left'] = node
      exprDict['op']   = self.getType()
      self.verify(oper)
      exprDict['right'] = self.loadShift(isDecl)
      node = BaseAST('EXPR', [], exprDict)
      
    return node
    
  def loadShift(self,isDecl):
    # Load (TERM (SHIFT_OPER TERM)*)
    exprDict = dict()
    node = self.loadTerm(isDecl)
    
    oper = ['SHIFT_OPER']
    while (self.check(oper)):
      # Create new expr node
      exprDict['left'] = node
      exprDict['op']   = self.getType()
      self.verify(oper)
      exprDict['right'] = self.loadTerm(isDecl)
      node = BaseAST('EXPR', [], exprDict)
      
    return node
    
  def loadTerm(self,isDecl):
    # Load (FACT ((ADD_SUB_OPER | CAT) FACT)*)
    exprDict = dict()
    node = self.loadFactor(isDecl)
    
    oper = ['ADD_SUB_OPER','CAT']
    while (self.check(oper)):
      # Create new expr node
      exprDict['left'] = node
      exprDict['op']   = self.getType()
      self.verify(oper)
      exprDict['right'] = self.loadFactor(isDecl)
      node = BaseAST('EXPR', [], exprDict)
      
    return node
    
  def loadFactor(self,isDecl):
    # Load (EXPONENT ((STAR | DIV | MOD_REM_OPER) EXPONENT)*)
    exprDict = dict()
    node = self.loadExponent(isDecl)
    
    oper = ['STAR','DIV','MOD_REM_OPER']
    while (self.check(oper)):
      # Create new expr node
      exprDict['left'] = node
      exprDict['op']   = self.getType()
      self.verify(oper)
      exprDict['right'] = self.loadExponent(isDecl)
      node = BaseAST('EXPR', [], exprDict)
      
    return node
    
  def loadExponent(self,isDecl):
    # Load (UNARY (EXP UNARY)*)
    exprDict = dict()
    node = self.loadUnary(isDecl)
    
    oper = ['EXP_OPER']
    while (self.check(oper)):
      # Create new expr node
      exprDict['left'] = node
      exprDict['op']   = self.getType()
      self.verify(oper)
      exprDict['right'] = self.loadUnary(isDecl)
      node = BaseAST('EXPR', [], exprDict)
      
    return node
    
  def loadUnary(self,isDecl):
    # Load ((ADD_SUB_OPER | NOT_OPER)? PRIMARY)
    exprDict = dict()
    
    oper = ['ADD_SUB_OPER','NOT_OPER']
    if (self.check(oper)):
      # Create new expr node
      exprDict['left'] = None
      exprDict['op']   = self.getType()
      self.verify(oper) 
      exprDict['right'] = self.loadPrimary(isDecl)
      node = BaseAST('EXPR', [], exprDict)
    else:
      node = self.loadPrimary(isDecl)
      
    return node
    
  def loadPrimary(self,isDecl):
    # Load (CONST | REPLICATE | (LPAREN SIMP_EXPR RPAREN) | FUNC | VAR)
    constList = ['INTEGER','FLOAT','BIT_INIT_HEX','BIT_INIT_BIN','STRING']
    funcList  = ['ID','LOGICAL_OPER','SHIFT_OPER','MOD_REM_OPER','NOT_OPER']
    if (self.check(constList)):
      return self.loadConst(isDecl)
    elif (self.check('LCURBRAC')):
      return self.loadReplicate(isDecl)
    elif (self.check('LPAREN')):
      return self.loadSimpleExpr(isDecl)
    elif (self.check(funcList)):
      # We dont know if it is function or variable
      if (self.peek().type == 'LPAREN'):
        return self.loadFuncCall()
      else:
        return self.loadVar(isDecl)
    
  def loadFuncCall(self,isDecl):
    # Load (FUNC_LIST CALL_ARG_LIST)
    funcList  = ['ID', 'LOGICAL_OPER', 'RELATION_OPER', 'SHIFT_OPER', 'ADD_SUB_OPER', 'STAR', 'DIV', 'MOD_REM_OPER', 'EXP_OPER', 'NOT_OPER']
    self.verify(funcList)
    funcDict = {'args': self.loadCallArgList(isDecl)}
    
    return BaseAST('FUNCCALL',[],funcDict)
  
  def loadReplicate(self,isDecl):
    # Load (VAR LCURBRAC SIMP_EXPR RCURBRAC)
    self.verify('LCURBRAC')
    expr = self.loadSimpleExpr(isDecl)
    self.verify('RCURBRAC')
    
    #TODO: What do I return
    return None
    
      
  def loadConst(self, isDecl):
    # CONST = (INTEGER | FLOAT | BIT_INIT | STRING)
    constList = ['INTEGER','FLOAT','BIT_INIT_HEX','BIT_INIT_BIN','STRING']
    
    numDict = dict()
    typeStr = self.getType()
    valStr = self.getValue()
    numDict['type']  = typeStr
    
    # Convert value
    if (typeStr == 'INTEGER'):
      numDict['value'] = [int(valStr)]
      numDict['array'] = [[0,0]]
    elif (typeStr == 'FLOAT'):
      numDict['value'] = [float(valStr)]
      numDict['array'] = [[0,0]]
    elif (typeStr == 'BIT_INIT_BIN'):
      numDict['type'] = 'BIT_INIT'
      binData = re.match('[b]?\'([01ZXLH-]+)\'',valStr).group(1)
      numDict['value'] = binData
      numDict['array'] = [[len(binData)-1,0]]
    elif (typeStr == 'BIT_INIT_HEX'):
      numDict['type'] = 'BIT_INIT'
      hexData = re.match('x\'([0-9a-fA-F]+)\'',valStr).group(1)
      binData = bin(int(hexData, 16))[2:].zfill(4*len(hexData))
      numDict['value'] = binData
      numDict['array'] = [[len(binData)-1,0]]
    elif (typeStr == 'STRING'):
      numDict['value'] = valStr
      numDict['array'] = [[0,0]]
    
    numDict['const'] = True
    numDict['decl']  = isDecl
    self.verify(constList)
    return BaseAST('CONST', [], numDict)
    
  def loadVar(self, isDecl):
    #Load (ID (INDEX_LIST)? (DOT VAR)?)
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
      # Check for field or attribute
      attrList = ['DIM','RANGE','LENGTH','LEFT','RIGHT']
      if (self.check(attrList)):
        # Load attribute
        varDict['field'] = None
        varDict['attr']  = self.loadAttr(isDecl)
      else:
        # Recursively load fields
        varDict['field'] = self.loadVar(isDecl)
        varDict['attr']  = None
      
    else:
      varDict['field'] = None
      varDict['attr']  = None
      
      
    return BaseAST('VAR', [], varDict)
    
  def loadAttr(self, isDecl):
    # Load (LPAREN (SIMP_EXPR)? RPAREN)
    attrList = ['DIM','RANGE','LENGTH','LEFT','RIGHT']
    attrDict = {'attr': self.getType()}
    self.verify(attrList)
    self.verify('LPAREN')
    arg = []
    if (not self.check('RPAREN')):
      arg.append(self.loadSimpleExpr(isDecl))
      
    self.verify('RPAREN')
    attrDict['arg'] = arg
    
    return BaseAST('ATTR',[],attrDict)
    
  def loadIndexList(self, isDecl):
    # Load line (LBRACK INDEX RBRACK)*
    sliceList = []
    while (self.check('LBRACK')):
      self.verify('LBRACK')
      sliceList.append(self.loadIndex(isDecl))
      self.verify('RBRACK')
      
    return sliceList
    
  def loadIndex(self, isDecl):
    # Load line (SIMP_EXPR (COLON SIMP_EXPR)?)
    
    left  = self.loadSimpleExpr(isDecl)
    # Slice
    if (self.check('COLON')):
      self.verify('COLON')
      right = self.loadSimpleExpr(isDecl)
      
    # Index
    else:
      right = left
      
    return [left, right]
    

