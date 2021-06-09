from .Lexer import Lexer
from .Lexer import Token
import re
import numpy as np
from copy import deepcopy

def determineBits(intVal):
  if (intVal == 0):
    return 2
  else:
    return int(np.ceil(np.log2(abs(intVal)))+2)

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
    for var, val in iter(grammerDict.items()):
      setattr(self, var, val)
            
  def log(self,tabLevel=0):
    attr = []
    node = []
    lines = []
    lines.append('{0}{1}'.format(tabLevel*' ', self.base))
    lines.append('{0}{1}: {2}'.format((tabLevel+2)*' ', 'comments', self.comments))
    tabLevel += 2
    for var, val in iter(self.__dict__.items()):
      if (var in ['base', 'comments']):
        continue
      
      typeStr = type(val).__name__
      # Loop over list
      if (typeStr == 'list'):
        a,b = self.logList(tabLevel, var, val)
        node = node + a
        attr = attr + b
      elif (typeStr == 'BaseAST'):
        nodeList = val.log(tabLevel)
        nodeList[0] = '{0}{1}: '.format(tabLevel*' ', var)+ nodeList[0].lstrip()
        node = node + nodeList
      else:
        attr.append('{0}{1}: {2}'.format(tabLevel*' ', var, val))
        
    lines = lines + attr
    lines = lines + node
    
    return lines
    
  def logList(self, tabLevel, var, val, ind=[]):
    attr = []
    node = []
    for d in range(len(val)):
      valItem = val[d]
      if (type(valItem).__name__ == 'list'):
        tmpInd = ind + [d]
        a,b = self.logList(tabLevel, var, valItem, tmpInd)
        node = node + a
        attr = attr + b
      elif (type(valItem).__name__ == 'BaseAST'):
        tmpInd = ind + [d]
        nodeList = valItem.log(tabLevel)
        nodeList[0] = '{0}{1}{2}: '.format(tabLevel*' ', var, tmpInd)+ nodeList[0].lstrip()
        node = node + nodeList
      else:
        tmpInd = ind + [d]
        attr.append('{0}{1}{2}: {3}'.format(tabLevel*' ', var, tmpInd, valItem))
        
    #if not attr:
    #  attr.append('{0}{1}: []'.format(tabLevel*' ', var))
        
    return (node, attr)
    
def createIntNode(value):
  intConstDict = {}
  intConstDict['typeName']   = 'sint'
  intConstDict['params'] = determineBits(value)
  intConstDict['value']  = value
  intConstDict['name']   = 'const'
  intConstDict['const']  = True
  intConstDict['port']   = None
  intConstDict['decl']   = True
  
  return BaseAST('CONST',[],intConstDict)
  
def createBitArray(value):
  bitDictArray = []
  for val in value:
    bitDict = {}
    bitDict['typeName'] = 'bit'
    bitDict['params']   = []
    bitDict['value']    = val
    bitDict['name']     = 'const'
    bitDict['const']    = True
    bitDict['port']     = None
    bitDict['decl']     = True
    
    bitDictArray.append(BaseAST('CONST',[],bitDict))
    
  if len(bitDictArray) == 1:
    return bitDictArray[0]
  else:
    aggDict = {'nodes': bitDictArray}
    return BaseAST('ARRAY',[],aggDict)
    
defaultArray = [[createIntNode(0), createIntNode(0)]]

class SyntaxParser(object):
  def __init__(self, lexer):
    self.lexer = lexer
    self.token = self.lexer.get()
    self.scope = None
  
  def error(self, expectedTokenType=None):
    tType = self.getType()
    tVal = self.getValue()
    tScope = self.getScope()
    print('Unexpected syntax line #{0}: Value {1}'.format(self.token.lineNo, tVal))
    if (expectedTokenType is not None):
      print('Expected Token {0} but got {1}, value="{2}"'.format(expectedTokenType, tType, tVal))
      
    if (self.scope.get() != tScope): 
      print('Expected Scope {0} but got {1}'.format(self.scope.get(), tScope))
      
    #self.lexer.debug()
    raise Exception('Unexpected syntax')
  
  # Read next token
  def next(self):
    #Get next token
    self.token = self.lexer.get()
    
  # Peek at next token
  def peek(self, ind=0):
    return self.lexer.peek(ind)
      
  # Read next token, but skipping comments and EOL
  def skip(self):
    #Comment list
    comment = []
    
    #Get next token, skipping over comments
    while (self.check(['COMMENT', 'EOL'])):
      #Add comment to list
      if (self.check('COMMENT')):
        comment.append(self.getValue())
        
      self.next()
      
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
      scopeGood = self.checkScope()
    else:
      scopeGood = True
      
    # Determine if scope and token are good
    return (tokenGood and scopeGood)
    
  def checkScope(self):
    return (self.getScope() == self.scope.get())
    
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
    
    # get initial comments
    comments = self.skip()
    
    # Determine base scope
    self.scope = SimpleScope(self.getScope())
    
    # Check for modules, libraries, and imports
    nodes = []
    decl = ['MODULE','LIBRARY','IMPORT']
    while (self.check(decl,True)):
      if (self.getType() == 'MODULE'):
        nodes.append(self.loadModuleDecl())
      elif (self.getType() == 'LIBRARY'):
        nodes.append(self.loadLibraryDecl())
      elif (self.getType() == 'IMPORT'):
        nodes.append(self.loadImportDecl())
      
    fileDict['nodes']= nodes

    # Create Root Node
    return BaseAST('FILE', comments, fileDict)
    
  def loadImportDecl(self):
    # Load line IMPORT ID (DOT ID)?
    
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
      self.verify(['ID','ALL'])
    else:
      libDict['load'] = 'all'
    
    # Skip
    comment = self.skip()
          
    # No import line, move on
    return BaseAST(base, comment, libDict)
    
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
    decl = ['STRUCT','INTERFACE','FUNCTION','ENUM','ID','CONST']
    while (self.check(decl,True)):
      if (self.check('STRUCT')):
        nodes.append(self.loadStruct())
      elif (self.check('INTERFACE')):
        nodes.append(self.loadInterface())
      elif (self.check('FUNCTION')):
        nodes.append(self.loadFunction())
      elif (self.check(['ID','CONST'])):
        nodes.append(self.loadVarDecl('var'))
      elif (self.check('ENUM')):
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
      structDict['params'] = self.loadDeclArgList()
    else:
      structDict['params'] = []
      
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
      varType['params'] = self.loadCallArgList(True)
    else:
      varType['params'] = []
      
    # Determine array size
    varType['decl'] = True
    if (self.check('LBRACK')):
      varType['array'] = self.loadIndexList(True)
    else:
      varType['array'] = deepcopy(defaultArray)
    
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
      itfcDict['params'] = self.loadDeclArgList()
    else:
      itfcDict['params'] = []
      
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
      varType['params'] = self.loadCallArgList(True)
    else:
      varType['params'] = []
      
    # Determine array size
    varType['decl'] = True
    if (self.check('LBRACK')):
      varType['array'] = self.loadIndexList(True)
    else:
      varType['array'] = deepcopy(defaultArray)
      
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
    # Load line (FUNCTION OPER_LIST DECL_ARG_LIST COLON)
    # OPER_LIST = (ID|EXP_OPER|POST_OPER|CMPD_ARITH_ASSIGN|CMPD_LOGICAL_ASSIGN|RELATION_OPER|ADD_SUB_OPER|DIV|STAR|CAT|LOGICAL_OPER|SHIFT_OPER|MOD_REM_OPER|NOT_OPER)
    base = 'FUNCTION'
    self.verify('FUNCTION',True)
    funcDict = dict()
    
    funcDict['name'] = self.getValue()
    functionNames = ['ID', 'EXP_OPER',' POST_OPER', 'CMPD_ARITH_ASSIGN', 'CMPD_LOGICAL_ASSIGN', 'RELATION_OPER', 'ADD_SUB_OPER', 'DIV', 'STAR', 'CAT', 'LOGICAL_OPER', 'SHIFT_OPER', 'MOD_REM_OPER', 'NOT_OPER']
    self.verify(functionNames)
    
    #Load function arguments
    funcDict['params'] = self.loadDeclArgList()
      
    self.verify('COLON')
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    #Load function statements
    nodes = self.loadFuncStatements()
      
    #Return to original scope
    self.rmScope()
      
    #Return field node
    funcDict['statements'] = nodes
    return BaseAST(base, comment, funcDict)
    
  def loadCallArgList(self, isDecl):
    # Load line (LPAREN (SIMP_EXPR (COMMA SIMP_EXPR)*)? RPAREN)
    self.verify('LPAREN')
    
    # See if there are any arguments
    argNodes = []
    if (not self.check('RPAREN')):
      argNodes.append(self.loadSimpleExpr(isDecl))
      while (self.check('COMMA')):
        self.verify('COMMA')
        argNodes.append(self.loadSimpleExpr(isDecl))
      
    self.verify('RPAREN')
    return argNodes
    
  def loadDeclArgList(self):
    # Load line (LPAREN (DECL_ARG (COMMA DECL_ARG)*)? RPAREN)
    self.verify('LPAREN')
    
    argNodes = []
    # Does not require inputs
    if (self.check('RPAREN')):
      self.verify('RPAREN')
      return argNodes
    
    # Load vars
    argNodes.append(self.loadDeclArg())
    while (self.check('COMMA')):
      self.verify('COMMA')
      argNodes.append(self.loadDeclArg())
      
    self.verify('RPAREN')
    return argNodes
    
  def loadDeclArg(self):
    #Load line (TYPE (STAR)* ID (ASSIGN CPLX_EXPR)?)
    # Define variable
    varType = dict()
    varType['type'] = self.getValue()
    self.verify('ID')
    
    #Determine number of dimensions
    dim = 0
    while (self.check('STAR')):
      dim += 1
      self.verify('STAR')
      
    varType['dim'] = dim
    
    #Get name
    varType['name'] = self.getValue()
    self.verify('ID')
    
    #See if default values are set
    varType['value'] = None
    if (self.check('ASSIGN')):
      self.verify('ASSIGN')
      
      #Get default value
      varType['value'] = self.loadComplexExpr(True)
    
    return BaseAST('PARAM', [], varType)
      
  def loadModuleDecl(self):
    # Read module line (MODULE ID (LPAREN BLACKBOX RPAREN)? COLON)
    base = self.getType()
    self.verify('MODULE', True)
    modDict = dict()
    modDict['name'] = self.getValue()
    self.verify('ID')
    
    # See if module is blackbox
    if (self.check('LPAREN')):
      self.verify('LPAREN')
      self.verify('BLACKBOX')
      self.verify('RPAREN')
      modDict['blackbox'] = True
    else:
      modDict['blackbox'] = False
      
    self.verify('COLON')
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    # Check for generic declarations
    genDeclNodes = []
    if (self.check('GENERICS')):
      genDeclNodes = self.loadGenericDecl()
      
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
    archDict['declareBlock'] = None
    if (self.check('DECLARE')):
      #Next load signal definitions
      archDict['declareBlock'] = self.loadDeclareBlock()
    
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
    decl = ['STRUCT','INTERFACE','FUNCTION','ENUM','ID']
    while (self.check(decl,True)):
      if (self.check('STRUCT')):
        declNodes.append(self.loadStruct())
      elif (self.check('INTERFACE')):
        declNodes.append(self.loadInterface())
      elif (self.check('FUNCTION')):
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
        self.verify('CONST')
        varType['const'] = True
      else:
        varType['const'] = False
    elif (declType is 'gen'):
      varType['const'] = True
    elif (declType is 'port'):
      varType['const'] = False
    else:
      raise('LoadVarDecl parse error')
    
    
    # Define variable
    varType['typeName'] = self.getValue()
    self.verify('ID',True)
    
    # Determine type def
    if (self.check('LPAREN')):
      varType['params'] = self.loadCallArgList(True)
    else:
      varType['params'] = []
      
    # Determine array size
    varType['decl'] = True
    if (self.check('LBRACK')):
      varType['array'] = self.loadIndexList(True)
    else:
      varType['array'] = deepcopy(defaultArray)
      
    # Generic or not
    if (declType is 'gen'):
      varType['generic'] = True
    else:
      varType['generic'] = False
    
    # Only ports have interface types
    if (declType is 'port'):
      # Interface type
      varType['port'] = self.getValue()
      self.verify(['BASE_INTERFACE','EXT_INTERFACE','ID'])
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
        varType['value'] = None
    else:
      varType['value'] = None

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
    # (ASSIGNMENT|FOR|CASE|IF|MODULE_INST|SPRO|APRO|PRO|ASSERTION|RENAME_CALL)
    statementNodes = []
    tokenList = ['ID', 'FOR', 'IF', 'CASE', 'SPRO', 'APRO', 'PRO', 'ASSERT', 'RENAME']
    while (self.check(tokenList,True)):
      # Load all statements
      statementNodes.append(self.loadStatement(False))
    
    return statementNodes
    
  def loadFuncStatements(self):
    # Load function statements
    # (VAR_DECL|ASSIGNMENT|FOR|CASE|IF|ASSERTION|RETURN)
    statementNodes = []
    tokenList = ['ID', 'FOR', 'IF', 'CASE', 'ASSERT', 'RETURN']
    while (self.check(tokenList,True)):
      statementNodes.append(self.loadStatement(False))
    
    return statementNodes
    
  def loadProStatements(self):
    # Load process statements
    # (ASSIGNMENT|FOR|CASE|IF|ASSERTION)
    statementNodes = []
    tokenList = ['ID', 'FOR', 'IF', 'CASE', 'ASSERT']
    while (self.check(tokenList,True)):
      if (self.check('ID')):
        # Ensure not to load module inst.
        type = self.determineStatement()
        if (type is 'MODULE'):
          #Module inst, error
          raise Exception('Module instatiation detected in process')
        elif (type is 'VAR_DECL'):
          raise Exception('Variable declaration detected in process')
        
      # Load statement
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
      return self.loadFor(isPro)
      
    elif (self.check('IF')):
      return self.loadIf(isPro)
      
    elif (self.check('CASE')):
      return self.loadCase(isPro)
      
    elif (self.check('RENAME')):
      return self.loadRename()
      
    elif (self.check('ASSERT')):
      return self.loadAssert()
      
    elif (self.check('REPORT')):
      return self.loadReport()
      
    elif (self.check('RETURN')):
      return self.loadReturn()
      
    elif (self.check('CONST')):
      return self.loadVarDecl('var')
      
    elif (self.check('ID')):
      # If ID, determine if its a module inst., var declaration, or assignment
      type = self.determineStatement()
      if (type == 'MODULE'):
        return self.loadModuleInst()
        
      elif (type == 'VAR_DECL'):
        return self.loadVarDecl('var')
        
      elif (type == 'ASSIGNMENT'):
        return self.loadAssignment()
        
      else:
        print('Type {0} not parsed.'.format(type))
        self.error()
    else:
      print('Type {0} not parsed.'.format(self.getType()))
      self.error()
      
  def determineStatement(self):
    # Determine if its a module inst., var declaration, or assignment
    # MODULE_INST = ID ID (LPAREN ID RPAREN)? COLON
    # VAR_DECL = ID (CALL_ARG_LIST)? (INDEX_LIST)? ID (ASSIGN CMPX_EXPR)?
    # ASSIGNMENT = ID (INDEX_LIST)? (DOT VAR)? (ASSIGN|CMPD_ARITH_ASSIGN|CMPD_LOGICAL_ASSIGN|POST_OPER) CMPX_EXPR
    
    ind = 0
    token = self.peek(ind)
    
    asgnList = ['ASSIGN', 'CMPD_ARITH_ASSIGN', 'CMPD_LOGICAL_ASSIGN', 'POST_OPER']
    
    # See what next ID is
    if (token.type == 'ID'):
      # Must be module or decl
      token = self.peek(ind+1)
      if (token.type in ['LPAREN', 'COLON']):
        # Module
        return 'MODULE'
      elif (token.type in ['ASSIGN','EOL']):
        # Variable declaration
        return 'VAR_DECL'
      else:
        self.error()
    elif (token.type == 'LPAREN'):
      # Can only be decl
      return 'VAR_DECL'
    elif (token.type == 'LBRACK'):
      # Can be decl or assignment
      
      # Skip past all indexing
      while (self.peek(ind).type == 'LBRACK'):
        while (self.peek(ind).type != 'RBRACK'):
          ind += 1
          if (self.peek(ind).type is 'EOL'):
            self.error('RBRACK')
            
      # Now determere if decl or assignment
      token = self.peek(ind+1)
      if (token.type == 'ID'):
        return 'VAR_DECL'
      else:
        return 'ASSIGNMENT'
    elif (token.type in asgnList):
      return 'ASSIGNMENT'
    else:
      print('DetermineStatement: not good')
    
  def loadSpro(self):
    # Load line (SPRO ARG_LIST COLON)
    base = self.getType()
    self.verify('SPRO')
    sproDict = {'params': self.loadCallArgList(True)}
    self.verify('COLON')
    comment = self.skip()
    
    self.addScope()
    
    # Load process statements
    sproDict['statements'] = self.loadProStatements()
    
    # Make sure there were statements found
    if (not sproDict['statements']):
      raise Exception('Spro: No statements defined')
    
    self.rmScope()
    
    return BaseAST(base, comment, sproDict)
    
  def loadApro(self):
    # Load line (APRO ARG_LIST COLON)
    base = self.getType()
    self.verify('APRO')
    aproDict = {'params': self.loadCallArgList(True)}
    self.verify('COLON')
    comment = self.skip()
    
    self.addScope()
    
    # Load process statements
    aproDict['statements'] = self.loadProStatements()
    
    # Make sure there were statements found
    if (not aproDict['statements']):
      raise Exception('Apro: No statements defined')
    
    self.rmScope()
    
    return BaseAST(base, comment, aproDict)
    
  def loadPro(self):
    # Load line (PRO ARG_LIST COLON)
    base = self.getType()
    self.verify('PRO')
    proDict = {'params': self.loadCallArgList(True)}
    self.verify('COLON')
    comment = self.skip()
    
    self.addScope()
    
    # Load process statements
    proDict['statements'] = self.loadProStatements()
    
    # Make sure there were statements found
    if (not proDict['statements']):
      raise Exception('Pro: No statements defined')
    
    self.rmScope()
    
    return BaseAST(base, comment, proDict)
    
  def loadFor(self,isPro):
    # Load line (FOR ID IN (RANGE_EXPR|VAR) COLON)
    base = self.getType()
    self.verify('FOR')
    forDict = dict()
    forDict['ind'] = self.getValue()
    self.verify('ID')
    self.verify('ASSIGN')
    forDict['iter'] = self.loadSimpleExpr(False)
    self.verify('COLON')
    comment = self.skip()
    
    self.addScope()
    
    # Load process statements
    if (isPro):
      forDict['statements'] = self.loadProStatements()
    else:
      forDict['statements'] = self.loadLogicStatements()
      
    # Make sure there were statements found
    if (not forDict['statements']):
      raise Exception('For: No statements defined')
      
    self.rmScope()
    
    return BaseAST(base, comment, forDict)
    
  def loadIf(self,isPro):
    # Load line (IF LPAREN SIMP_EXPR RPAREN COLON)
    base = self.getType()
    self.verify('IF', True)
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
      
    # Make sure there were statements found
    if (not ifDict['statements']):
      raise Exception('If: No statements defined')
      
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
    self.verify('ELIF', True)
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
      
    # Make sure there were statements found
    if (not elifDict['statements']):
      raise Exception('Elif: No statements defined')
      
    self.rmScope()
    
    return BaseAST(base, comment, ifDict)
    
  def loadElse(self,isPro):
    # Load line (ELSE COLON)
    base = self.getType()
    self.verify('ELSE', True)
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
      
    # Make sure there were statements found
    if (not elseDict['statements']):
      raise Exception('Else: No statements defined')
      
    self.rmScope()
    
    return BaseAST(base, comment, elseDict)
    
  def loadCase(self,isPro):
    # Load line (CASE LPAREN SIMP_EXPR RPAREN COLON)
    base = self.getType()
    self.verify('CASE', True)
    self.verify('LPAREN')
    caseDict = {'arg': self.loadSimpleExpr(False)}
    self.verify('RPAREN')
    self.verify('COLON')
    comment = self.skip()
    
    self.addScope()
    
    # Loop over all choices within new scope
    caseChoices = []
    while(self.checkScope()):
      caseChoices.append(self.loadCaseChoice(isPro))
      
    # Make sure there were statements found
    if (not caseChoices):
      raise Exception('Case: No choices defined')
      
    caseDict['choices'] = caseChoices
    self.rmScope()
    
    return BaseAST(base, comment, caseDict)
    
  def loadCaseChoice(self,isPro):
    # Load line (CHOICE COLON)
    caseDict = dict()
    caseDict['choice'] = self.loadChoice(True)
    self.verify('COLON')
    comments = self.skip()
    
    self.addScope()
    
    # Load process or logic statements
    if (isPro):
      # Load process
      caseDict['statements'] = self.loadProStatements()
    else:
      # Load logic
      caseDict['statements'] = self.loadLogicStatements()
      
    # Make sure there were statements found
    if (not caseDict['statements']):
      raise Exception('Case Choice: No statements defined')
      
    self.rmScope()
      
    return BaseAST('CHOICE', comments, caseDict)
      
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
    else:
      baseInd = createIntNode(1)
      asgnDict['rightExpr'] = baseInd
      
    comment = self.skip()
    return BaseAST(operType, comment, asgnDict)
    
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
    modDict['gens'] = []
    if (self.check('GENERICS', True)):
      modDict['gens'] = self.loadGenericInst()
      
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
    while (self.check('ID', True)):
      # Create variable declaration
      genVars.append(self.loadGenVarInst())
      
    # Make sure there were statements found
    if (not genVars):
      raise Exception('Generic Inst: No statements defined')
      
    #Return to original scope
    self.rmScope()
      
    # No more generics
    return genVars
    
  def loadGenVarInst(self):
    # Load line (VAR ASSIGN CMPX_EXPR)
    varDict = dict()
    varDict['gen'] = self.loadVar(False)
    self.verify('ASSIGN')
    varDict['var'] = self.loadComplexExpr(False)
      
    comment = self.skip()
    return BaseAST('GEN_ASSIGN', comment, varDict)
    
  def loadPortInst(self):
    # Load line (PORTS COLON)
    self.verify('PORTS',True)
    self.verify('COLON')
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    # Loop over all ports
    portVars = []
    while (self.check('ID', True)):
      # Create port declaration
      portVars.append(self.loadPortVarInst())
      
    # Make sure there were statements found
    if (not portVars):
      raise Exception('Post Inst: No statements defined')
      
    #Return to original scope
    self.rmScope()
      
    return portVars
    
  def loadPortVarInst(self):
    # Load line (VAR ASSIGN CMPX_EXPR)
    varDict = dict()
    varDict['port'] = self.loadVar(False)
    self.verify('ASSIGN')
    varDict['var'] = self.loadComplexExpr(False)
      
    comment = self.skip()
    return BaseAST('PORT_ASSIGN', comment, varDict)
    
  def loadReturn(self):
    # Load line (RETURN (SIMP_EXPR|(LPAREN SIMP_EXPR (COMMA SIMP_EXPR)* RPAREN)))
    self.verify('RETURN',True)
    vars = []
    if (self.check('LPAREN')):
      self.verify('LPAREN')
      vars.append(self.loadSimpleExpr(False))
      
      while (self.check('COMMA')):
        vars.append(self.loadSimpleExpr(False))
        
      self.verify('RPAREN')
      
    else:
      vars.append(self.loadSimpleExpr(False))
      
    returnDict = {'vars': vars}
    comment = self.skip()
    
    return BaseAST('RETURN', comment, returnDict)
    
  def loadRename(self):
    # Load line (RENAME VAR ASSIGN SIMP_EXPR)
    base = self.getType()
    self.verify('RENAME', True)
    renameDict = dict()
    renameDict['var'] = self.loadVar(False)
    self.verify('ASSIGN')
    renameDict['name'] = self.loadSimpleExpr()
    
    # Line is complete
    comment = self.skip()
    
    return BaseAST(base, comment, renameDict)
    
    
  def loadAssert(self):
    # Load line (ASSERT SIMP_EXPR COLON)
    base = self.getType()
    self.verify('ASSERT', True)
    assertDict = dict()
    assertDict['condition'] = self.loadSimpleExpr(False)
    self.verify('COLON')
    
    # Line is complete
    comment = self.skip()
    
    # Read report statement
    self.addScope()
    assertDict['status'] = self.loadReport()
    self.rmScope()
    
    return BaseAST(base, comment, assertDict)
    
  def loadReport(self):
    # Load line ((PRINT|WARNING|ERROR) LPAREN CONST RPAREN)
    base = self.getType()
    reportDict = {}
    self.verify(['PRINT', 'WARNING', 'ERROR'], True)
    self.verify('LPAREN')
    reportDict['str'] = self.loadSimpleExpr(True)
    self.verify('RPAREN')
    
    # Line is complete
    comment = self.skip()
    
    return BaseAST(base, comment, reportDict)
    
  # isDecl specifies if this is a declaration call or assignment call
  # this variable will be passed to syntax checker to verify
  # array sizes are constant values. assignment array sizes can be 
  # constant or signal
  def loadComplexExpr(self,isDecl):
    # Load (AGGREGATE | SIMP_EXPR)
    if (self.check('LCURBRAC')):
      return self.loadArray(isDecl)
    else:
      return self.loadSimpleExpr(isDecl)
    
  def loadArray(self,isDecl):
    # Load line (LCURBRAC ELEM_ASSOC (COMMA ELEM_ASSOC)* RCURBRAC)
    comments = []
    self.verify('LCURBRAC')
    comments += self.skip()
    args = [self.loadComplexExpr(isDecl)]
    while (self.check('COMMA')):
      self.verify('COMMA')
      comments += self.skip()
      args.append(self.loadComplexExpr(isDecl))
      comments += self.skip()
      
    self.verify('RCURBRAC')
    
    aggDict = {'nodes': args}
    
    return BaseAST('ARRAY', comments, aggDict)
    
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
    # Load (INDEX|OTHERS)
    if (self.check('OTHERS')):
      arg = BaseAST('OTHERS', [], dict())
      self.verify('OTHERS')
    else:
      arg = self.loadSimpleExpr(isDecl)
        
    return arg
    
  def loadSimpleExpr(self,isDecl):
    # Load (RELATION (LOGICAL_OPER RELATION)*)
    node = self.loadRelation(isDecl)
    
    oper = ['LOGICAL_OPER']
    while (self.check(oper)):
      # Create new expr node
      exprDict = dict()
      exprDict['op']   = self.getValue()
      self.verify(oper)
      exprDict['params'] = [node, self.loadRelation(isDecl)]
      node = BaseAST('EXPR', [], exprDict)
      
    # See if units are defined
    node.units = None
    if (self.check('ID')):
      node.type = 'time'
      node.units = self.getValue()
      self.verify('ID')
      
    return node
  
  def loadRelation(self,isDecl):
    # Load (SHIFT (RELATION_OPER SHIFT)*)
    node = self.loadShift(isDecl)
    
    oper = ['RELATION_OPER']
    while (self.check(oper)):
      # Create new expr node
      exprDict = dict()
      exprDict['op']   = self.getValue()
      self.verify(oper)
      exprDict['params'] = [node, self.loadShift(isDecl)]
      node = BaseAST('EXPR', [], exprDict)
      
    return node
    
  def loadShift(self,isDecl):
    # Load (TERM (SHIFT_OPER TERM)*)
    node = self.loadTerm(isDecl)
    
    oper = ['SHIFT_OPER']
    while (self.check(oper)):
      # Create new expr node
      exprDict = dict()
      exprDict['op']   = self.getValue()
      self.verify(oper)
      exprDict['params'] = [node, self.loadTerm(isDecl)]
      node = BaseAST('EXPR', [], exprDict)
      
    return node
    
  def loadTerm(self,isDecl):
    # Load (FACT ((ADD_SUB_OPER | CAT) FACT)*)
    node = self.loadFactor(isDecl)
    
    oper = ['ADD_SUB_OPER','CAT']
    while (self.check(oper)):
      # Create new expr node
      exprDict = dict()
      exprDict['op']   = self.getValue()
      if (self.getType() == 'CAT'):
        op = 'CAT'
      else:
        op = 'EXPR'
      self.verify(oper)
      exprDict['params'] = [node, self.loadFactor(isDecl)]
      node = BaseAST(op, [], exprDict)
      
    return node
    
  def loadFactor(self,isDecl):
    # Load (EXPONENT ((STAR | DIV | MOD_REM_OPER) EXPONENT)*)
    node = self.loadExponent(isDecl)
    
    oper = ['STAR','DIV','MOD_REM_OPER']
    while (self.check(oper)):
      # Create new expr node
      exprDict = dict()
      exprDict['op']   = self.getValue()
      self.verify(oper)
      exprDict['params'] = [node, self.loadExponent(isDecl)]
      node = BaseAST('EXPR', [], exprDict)
      
    return node
    
  def loadExponent(self,isDecl):
    # Load (UNARY (EXP UNARY)*)
    node = self.loadUnary(isDecl)
    
    oper = ['EXP_OPER']
    while (self.check(oper)):
      # Create new expr node
      exprDict = dict()
      exprDict['op']   = self.getValue()
      self.verify(oper)
      exprDict['params'] = [node, self.loadUnary(isDecl)]
      node = BaseAST('EXPR', [], exprDict)
      
    return node
    
  def loadUnary(self,isDecl):
    # Load ((ADD_SUB_OPER | NOT_OPER)? PRIMARY)
    exprDict = dict()
    
    oper = ['ADD_SUB_OPER','NOT_OPER']
    if (self.check(oper)):
      # Create new expr node
      exprDict = dict()
      exprDict['op']   = self.getValue()
      self.verify(oper)
      exprDict['params'] = [self.loadPrimary(isDecl)]
      node = BaseAST('EXPR', [], exprDict)
    else:
      node = self.loadPrimary(isDecl)
      
    return node
    
  def loadPrimary(self,isDecl):
    # Load (CONST | REPLICATE | (LPAREN SIMP_EXPR RPAREN) | FUNC | VAR)
    constList = ['INTEGER', 'FLOAT', 'BIT_INIT_HEX', 'BIT_INIT_BIN', 'STRING', 'BOOLEAN']
    funcList  = ['ID','LOGICAL_OPER','SHIFT_OPER','MOD_REM_OPER','NOT_OPER']
    if (self.check(constList)):
      return self.loadConst(isDecl)
      
    elif (self.check('LCURBRAC')):
      return self.loadReplicate(isDecl)
      
    elif (self.check('LPAREN')):
      self.verify('LPAREN')
      expr = self.loadSimpleExpr(isDecl)
      self.verify('RPAREN')
      return expr
      
    elif (self.check(funcList)):
      # We dont know if it is function or variable
      if (self.peek().type == 'LPAREN'):
        return self.loadFuncCall(isDecl)
      else:
        return self.loadVar(isDecl)
    
  def loadFuncCall(self,isDecl):
    # Load (FUNC_LIST CALL_ARG_LIST)
    funcList  = ['ID', 'LOGICAL_OPER', 'RELATION_OPER', 'SHIFT_OPER', 'ADD_SUB_OPER', 'STAR', 'DIV', 'MOD_REM_OPER', 'EXP_OPER', 'NOT_OPER']
    funcDict = {'name': self.getValue()}
    self.verify(funcList)
    funcDict['params'] = self.loadCallArgList(isDecl)
    
    return BaseAST('FUNCCALL',[],funcDict)
    
  def loadAttrCall(self,isDecl):
    # Load (ID CALL_ARG_LIST)
    attrDict = {'name': self.getValue()}
    self.verify('ID')
    attrDict['params'] = self.loadCallArgList(isDecl)
    
    return BaseAST('ATTRCALL',[],attrDict)
  
  def loadReplicate(self,isDecl):
    # Load (VAR LCURBRAC SIMP_EXPR RCURBRAC)
    self.verify('LCURBRAC')
    expr = self.loadSimpleExpr(isDecl)
    self.verify('RCURBRAC')
    
    #TODO: What do I return
    return 1
    
      
  def loadConst(self, isDecl):
    # CONST = (INTEGER | FLOAT | BIT_INIT | STRING)
    constList = ['INTEGER', 'FLOAT', 'BIT_INIT_HEX', 'BIT_INIT_BIN', 'STRING', 'BOOLEAN']
    
    numDict = dict()
    typeStr = self.getType()
    valStr = self.getValue()
    
    # Convert value
    if (typeStr == 'INTEGER'):
      value = int(valStr)
      numDict['typeName'] = 'sint'
      numDict['params'] = [determineBits(value)]
      numDict['value']  = value
    elif (typeStr == 'FLOAT'):
      numDict['typeName']  = 'float'
      numDict['params'] = []
      numDict['value'] = float(valStr)
    elif (typeStr == 'BIT_INIT_BIN'):
      #numDict['typeName'] = 'bit'
      #numDict['params'] = []
      binData = re.match('[b]?\'([01ZXLH-]+)\'',valStr).group(1)
      self.verify(constList)
      return createBitArray(binData)
      #numDict['value'] = list(binData)
    elif (typeStr == 'BIT_INIT_HEX'):
      #numDict['typeName'] = 'bit'
      #numDict['params'] = []
      hexData = re.match('x\'([0-9a-fA-F]+)\'',valStr).group(1)
      binData = bin(int(hexData, 16))[2:].zfill(4*len(hexData))
      self.verify(constList)
      return createBitArray(binData)
      #numDict['value'] = list(binData)
    elif (typeStr == 'STRING'):
      numDict['typeName']  = 'str'
      numDict['params'] = []
      numDict['value'] = valStr.replace('"','')
    elif (typeStr == 'BOOLEAN'):
      numDict['typeName']  = 'bool'
      numDict['params'] = []
      numDict['value'] = valStr
    
    numDict['name']  = 'const'
    numDict['const'] = True
    numDict['port']  = None
    numDict['decl']  = isDecl
    self.verify(constList)
    
    return BaseAST('CONST', [], numDict)
    
  def loadVar(self, isDecl):
    #Load (ID (INDEX_LIST)? (DOT VAR)? ) 
    varDict = dict()
    varDict['name'] = self.getValue()
    self.verify('ID')
    
    varDict['decl'] = isDecl
    
    # check slice
    if (self.check('LBRACK')):
      varDict['array'] = self.loadIndexList(isDecl)
    else:
      varDict['array'] = None
      
    # check for struct or interface variable
    if (self.check('DOT')):
      self.verify('DOT')
      if (self.check('ID') and (self.peek().type == 'LPAREN')):
        # Load attribute
        varDict['field'] = None
        varDict['attr']  = self.loadAttrCall(isDecl)
      elif (self.check('ID')):
        # Recursively load fields
        varDict['field'] = self.loadVar(isDecl)
        varDict['attr']  = None
      
    else:
      varDict['field'] = None
      varDict['attr']  = None
      
    return BaseAST('VAR', [], varDict)
    
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
      return [left, self.loadSimpleExpr(isDecl)]
      
    # Index
    else:
      return [left]
      
