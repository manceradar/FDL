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
    
    if (self.base is 'CONST'):
      lines.append(self.logConst())
      return lines
    
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
    
  def logConst(self):
    # special case for const to reduce lines down
    base = self.base
    type = self.typeName
    typeParam = self.params
    typeParam = str(typeParam)[1:-1]
    value = self.value
    return '{0} {1}({2}) = {3}'.format(base, type, typeParam, value)
    
def createIntNode(value):
  intConstDict = {}
  intConstDict['typeName']   = 'uint'
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
    return BaseAST('AGGREGATE',[],aggDict)
    
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
    print('Unexpected syntax: line #{0} (Value: {1})'.format(self.token.lineNo, tVal))
    print(self.lexer.getTextLine(self.token.lineNo))
    print(' '*self.token.charNo + '^')
    print(' '*self.token.charNo + '|')
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
    while (self.check(['COMMENT', 'COMMENT_HEADER', 'COMMENT_FMT', 'EOL'])):
      #Add comment to list
      if (self.check(['COMMENT', 'COMMENT_HEADER', 'COMMENT_FMT'])):
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
    decl = ['IMPORT', 'MODULE', 'ARCH', 'LIBRARY', 'STRUCT', 'INTERFACE', 'TRAIT', 'IMPL', 'FUNC', 'TASK', 'ENUM', 'CONST', 'ATTR']
    while (self.check(decl,True)):
      self.checkScope()
      if (self.getType() == 'IMPORT'):
        nodes.append(self.loadImportDecl())
      elif (self.getType() == 'MODULE'):
        nodes.append(self.loadModuleDecl())
      elif (self.getType() == 'ARCH'):
        nodes.append(self.loadArchDecl())
      elif (self.getType() == 'LIBRARY'):
        nodes.append(self.loadLibraryDecl())
      elif (self.getType() == 'STRUCT'):
        nodes.append(self.loadStructDecl())
      elif (self.getType() == 'INTERFACE'):
        nodes.append(self.loadInterfaceDecl())
      elif (self.getType() == 'TRAIT'):
        nodes.append(self.loadTraitDecl())
      elif (self.getType() == 'IMPL'):
        nodes.append(self.loadImplDecl())
      elif (self.getType() == 'FUNC'):
        nodes.append(self.loadFunctionDecl())
      elif (self.getType() == 'TASK'):
        nodes.append(self.loadTaskDecl())
      elif (self.getType() == 'ENUM'):
        nodes.append(self.loadEnumDecl())
      elif (self.getType() == 'CONST'):
        nodes.append(self.loadVarDecl('const'))
      elif (self.getType() == 'ATTR'):
        nodes.append(self.loadAttrDecl())
      else:
        self.error()
      
    fileDict['nodes']= nodes

    # Create Root Node
    return BaseAST('FILE', comments, fileDict)
    
  def loadBaseDecl(self):
    # Loop over all declarations
    declNodes =[]
    decl = ['STRUCT', 'INTERFACE', 'TRAIT', 'IMPL', 'FUNC', 'TASK', 'ENUM', 'ATTR', 'ID', 'CONST']
    while (self.check(decl,True)):
      # Verify scope
      self.checkScope()
      
      if (self.check('STRUCT')):
        declNodes.append(self.loadStructDecl())
      elif (self.check('INTERFACE')):
        declNodes.append(self.loadInterfaceDecl())
      elif (self.check('TRAIT')):
        declNodes.append(self.loadTraitDecl())
      elif (self.check('IMPL')):
        declNodes.append(self.loadImplDecl())
      elif (self.check('FUNC')):
        declNodes.append(self.loadFunctionDecl())
      elif (self.check('TASK')):
        declNodes.append(self.loadTaskDecl())
      elif (self.check('CONST')):
        declNodes.append(self.loadVarDecl('const'))
      elif (self.check('ID')):
        declNodes.append(self.loadVarDecl('signal'))
      elif (self.check('ATTR')):
        declNodes.append(self.loadAttrDecl())
      elif (self.check('ENUM')):
        declNodes.append(self.loadEnumDecl())
        
    return declNodes
    
  def loadDeclareBlock(self):
    #Load line (DECLARE COLON)
    
    # Verify scope
    self.checkScope()
    
    base = self.getType()
    self.verify('DECLARE',True)
    self.verify('COLON')
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    declNodes = self.loadBaseDecl()
      
    declDict = {'declNodes': declNodes}
    
    #Return to original scope
    self.rmScope()
    
    return BaseAST(base, comment, declDict)
    
  def loadLogicBlock(self, logicType):
    #Load line (LOGIC COLON)
    
    # Verify scope
    self.checkScope()
    
    base = self.getType()
    self.verify('LOGIC',True)
    self.verify('COLON')
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    if (logicType is 'arch'):
      nodes = self.loadArchStatements()
    elif (logicType is 'func'):
      nodes = self.loadFuncStatements()
    elif (logicType is 'task'):
      nodes = self.loadTaskStatements()
    
    # Load logic statements
    logicDict = {'statements': nodes}
    
    #Return to original scope
    self.rmScope()
    
    return BaseAST(base, comment, logicDict)
    
  def loadImportDecl(self):
    # Load line IMPORT ID (DOT ID)* (AS ID)?
    
    # Create import dict
    importDict = dict()
    base = self.getType()
    self.verify('IMPORT')
    importDict['load'] = [self.getValue()]
    self.verify('ID')
      
    # Check if DOT is used to only load one item
    while (self.check('DOT')):
      self.verify('DOT')
      importDict['load'].append(self.getValue())
      self.verify('ID')
      
    # Check if rename
    if (self.check('AS')):
      self.verify('AS')
      importDict['name'] = self.getValue()
      self.verify('ID')
    else:
      importDict['name'] = importDict['load'][-1]
    
    # Skip
    comment = self.skip()
          
    # No import line, move on
    return BaseAST(base, comment, importDict)
    
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
    nodes = self.loadBaseDecl()
        
    #Done and decrease scope
    self.rmScope()
    
    libDict['nodes'] = nodes
    
    return BaseAST(base, comment, libDict)
    
  def loadStructDecl(self):
    # Load line (INTERFACE ID GEN_TYPE_DECL? DECL_ARG_LIST? COLON)
    base = self.getType()
    self.verify('STRUCT')
    structDict = dict()
    structDict['name'] = self.getValue()
    self.verify('ID')
    
    # See if structure has generic types
    if (self.check('LT')):
      structDict['generics'] = self.loadGenTypeDecl()
    else:
      structDict['generics'] = []
    
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
      # Verify scope
      self.checkScope()
      
      #Load Field
      nodes.append(self.loadVarDecl('struct'))
      
    #Return to original scope
    self.rmScope()
      
    #Return field node
    structDict['fieldNodes'] = nodes
    return BaseAST(base, comment, structDict)
    
  def loadInterfaceDecl(self):
    # Load line (INTERFACE ID GEN_TYPE_DECL? DECL_ARG_LIST? COLON)
    base = self.getType()
    self.verify('INTERFACE')
    itfcDict = dict()
    itfcDict['name'] = self.getValue()
    self.verify('ID')
    
    # See if interface has generic types
    if (self.check('LT')):
      itfcDict['generics'] = self.loadGenTypeDecl()
    else:
      itfcDict['generics'] = []
    
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
      # Verify scope
      self.checkScope()
      
      #Load Field
      nodes.append(self.loadVarDecl('interface'))
      
    #Return to original scope
    self.rmScope()
      
    #Return field node
    itfcDict['fieldNodes'] = nodes
    return BaseAST(base, comment, itfcDict)
    
  def loadTraitDecl(self):
    # Load line (TRAIT ID GEN_TYPE_DECL? COLON)
    base = self.getType()
    self.verify('TRAIT')
    traitDict = dict()
    traitDict['name'] = self.getValue()
    self.verify('ID')
    
    # See if trait has generic types
    if (self.check('LT')):
      traitDict['generics'] = self.loadGenTypeDecl()
    else:
      traitDict['generics'] = []
      
    self.verify('COLON')
    comment = self.skip()
    
    self.addScope()
    
    #Load fields
    nodes = self.loadTraitImplStatements()
      
    #Return to original scope
    self.rmScope()
      
    #Return field node
    traitDict['nodes'] = nodes
    return BaseAST(base, comment, traitDict)
    
  def loadImplDecl(self):
    # There are two types of implementations
    # TRAIT_NAME = ID (DOT ID)*
    # STR_INT_NAME = ID (DOT ID)*
    # INHERENT_IMPL = IMPL (GEN_TYPE_DECL)? STR_INT_NAME (GEN_TYPE_CALL)? COLON
    # TRAIT_IMPL = IMPL (GEN_TYPE_DECL)? TRAIT_NAME (GEN_TYPE_CALL)? FOR STR_INT_NAME (GEN_TYPE_CALL)? COLON
    base = self.getType()
    self.verify('IMPL')
    implDict = dict()
    
    # See if output has generic types
    if (self.check('LT')):
      implDict['outGeneric'] = self.loadGenTypeDecl()
    else:
      implDict['outGeneric'] = []
    
    # At this point, we are unsure if it is a inherent impl or trait impl
    idName = self.loadBaseName('NAME')
    
    # See if type/trait has generic types
    if (self.check('LT')):
      genNode = self.loadGenTypeCall()
    else:
      genNode = []
      
    if (self.check('FOR')):
      self.verify('FOR')
      name = self.loadBaseName('NAME')
      # See if output has generic types
      if (self.check('LT')):
        typeGen = self.loadGenTypeCall()
      else:
        typeGen = []
        
      # Pack data
      implDict['name'] = name
      implDict['typeGeneric'] = typeGen
      implDict['traitImpl'] = True
      implDict['traitName'] = idName
      implDict['traitGeneric'] = genNode
    else:
      # No more info, pack data
      implDict['name'] = idName
      implDict['typeGeneric'] = genNode
      implDict['traitImpl'] = False
      implDict['traitName'] = ''
      implDict['traitGeneric'] = []
      
    if (implDict['traitImpl'] and not self.check('COLON')):
      # For trait implementations, statements are not necessary 
      # This is due to some traits with all inherent functions
      implDict['nodes'] = []
      return BaseAST(base, comment, implDict)
      
    
    self.verify('COLON')
    comment = self.skip()
    
    self.addScope()
    
    #Load fields
    nodes = self.loadTraitImplStatements()
      
    #Return to original scope
    self.rmScope()
      
    #Return field node
    implDict['nodes'] = nodes
    return BaseAST(base, comment, implDict)
    
  def loadTraitImplStatements(self):
    # Load trait statements
    # (CONST_VAR_DECL | ATTR_DECL | FUNC_DEF | FUNC_DECL | TASK_DEF | TASK_DECL)
    declNodes =[]
    decl = ['FUNC', 'TASK', 'ATTR', 'CONST']
    while (self.check(decl,True)):
      # Verify scope
      self.checkScope()
      
      if (self.check('FUNC')):
        declNodes.append(self.loadFunctionDecl(includeSelf=True))
      elif (self.check('TASK')):
        declNodes.append(self.loadTaskDecl(includeSelf=True))
      elif (self.check('CONST')):
        declNodes.append(self.loadVarDecl('const'), includeSelf=True)
      elif (self.check('ATTR')):
        declNodes.append(self.loadAttrDecl(includeSelf=True))
        
    return declNodes
    
  def loadVarDecl(self, declType, includeSelf=False):
    # TYPE_DECL = TYPE_NAME GEN_TYPE_DECL? CALL_ARG_LIST? INDEX_LIST?
    # TYPE_NAME = ID (DOT ID)*
    # VAR_DECL = TYPE_DECL ID
    # 
    # GEN_DECL = VAR_DECL (ASSIGN CMPX_EXPR)?
    # PORT_DECL = TYPE_DECL (BASE_INTERFACE|EXT_INTERFACE) ID
    # STRUCT_FIELD = VAR_DECL (ASSIGN CMPX_EXPR)?
    # INTERFACE_FIELD = TYPE_DECL EXT_INTERFACE ID
    # CONST_VAR_DECL = CONST VAR_DECL ASSIGN CMPX_EXPR
    # SIGNAL_VAR_DECL = (CONST)? VAR_DECL (ASSIGN CMPX_EXPR)?
    varType = dict()
    
    if (declType not in ['gen', 'port', 'struct', 'interface', 'const', 'signal']):
      raise('loadVarDecl parse error')
    
    # Verify scope
    self.checkScope()
    
    # Determine if const variable
    if (declType is 'signal'):
      if (self.check('CONST')):
        self.verify('CONST')
        varType['const'] = True
      else:
        varType['const'] = False
    elif (declType is 'gen'):
      varType['const'] = True
    elif (declType is 'port'):
      varType['const'] = False
    elif (declType is 'const'):
      self.verify('CONST')
      varType['const'] = True
    elif (declType is 'struct'):
      varType['const'] = False
    elif (declType is 'interface'):
      varType['const'] = False
    
    
    # Define variable
    varType['typeName'] = self.loadBaseName('TYPE', includeSelf) # No
      
    # See if module has generic types
    if (self.check('LT')):
      varType['typeGenerics'] = self.loadGenTypeDecl()
    else:
      varType['typeGenerics'] = []
    
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
    
    # Only ports and interfaces have interface types
    if (declType is 'port'):
      # Interface type
      varType['port'] = self.getValue()
      self.verify(['BASE_INTERFACE','EXT_INTERFACE'])
    elif (declType is 'interface'):
      # Interface type
      varType['port'] = self.getValue()
      self.verify('EXT_INTERFACE')
    else:
      varType['port'] = None
    
    # Name
    varType['name'] = self.getValue()
    self.verify('ID')
    
    # Only variables and gen can have initial values
    if (declType in ['gen', 'struct', 'const', 'signal']):
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
    
    if (declType in ['struct','interface']):
      return BaseAST('FIELD', comment, varType)
    else:
      return BaseAST('DECL', comment, varType)
    
  def loadEnumDecl(self):
    # Load (ENUM ID ASSIGN LPAREN ID (COMMA ID)* RPAREN)
    self.verify('ENUM')
    enumDict = dict()
    enumDict['name'] = self.getValue()
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
    
    return BaseAST('ENUM',comment,enumDict)
    
  def loadAttrDecl(self, includeSelf=False):
    # Load (ATTR_DECL = ATTR LPAREN ATTR_SPEC (COMMA ATTR_SPEC)* RPAREN FOR TYPE_NAME)
    self.verify('ATTR')
    attrDict = dict()
    self.verify('LPAREN')
    
    # Load states
    nodes = [self.loadAttrSpec()]
    while (self.check('COMMA')):
      self.verify('COMMA')
      nodes.append(self.loadAttrSpec())
      
    self.verify('RPAREN')
    attrDict['spec'] = nodes
    
    self.verify('FOR')
    attrDict['name'] = self.loadBaseName('NAME',includeSelf) # Yes
    
    comment = self.skip()
    
    return BaseAST('ATTR', comment, attrDict)
    
  def loadAttrSpec(self):
    # Load (ATTR_SPEC = ID ASSIGN SIMP_EXPR)
    specDict = dict()
    specDict['name'] = self.getValue()
    self.verify('ID')
    self.verify('ASSIGN')
    specDict['value'] = self.loadSimpleExpr(False)
    
    return BaseAST('ATTRSPEC', [], specDict)
    
  def loadFunctionDecl(self, includeSelf=False):
    # Load line FUNC_DEF = FUNC FUNC_NAME GEN_TYPE_DECL? DECL_ARG_LIST? RARROW RETURN_TYPE
    # FUNC_DECL = FUNC_DEF COLON
    # FUNC_NAME = (ID | LOGICAL_OPER | MOD_REM_OPER | NOT_OPER)
    # FUNC_STMT = (DECLARE_DECL BASE_DECL_STMT)? LOGIC_DECLARE FUNC_LOGIC_STMT
    
    base = 'FUNC'
    self.verify('FUNC',True)
    funcDict = dict()
    
    funcDict['name'] = self.getValue()
    functionNames = ['ID', 'RELATION_OPER', 'LOGICAL_OPER', 'MOD_REM_OPER', 'NOT_OPER']
    self.verify(functionNames)
    
    # See if trait has generic types
    if (self.check('LT')):
      funcDict['generics'] = self.loadGenTypeDecl()
    else:
      funcDict['generics'] = []
    
    #Load function arguments
    funcDict['params'] = self.loadDeclArgList(includeSelf)
    
    # Load return type
    self.verify('RARROW')
    funcDict['returnType'] = self.loadReturnType(includeSelf)
      
    if self.check('COLON'):
      self.verify('COLON')
      funcDict['funcDef'] = False
    else:
      funcDict['funcDef'] = True
      comment = self.skip()
      return BaseAST(base, [], funcDict)
    
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    # Check if declare block exists
    funcDict['declareBlock'] = None
    if (self.check('DECLARE')):
      #Next load signal definitions
      funcDict['declareBlock'] = self.loadDeclareBlock()
    
    #Next load logic
    funcDict['logicBlock'] = self.loadLogicBlock('func')
      
    #Return to original scope
    self.rmScope()
      
    return BaseAST(base, comment, funcDict)
    
  def loadTaskDecl(self, includeSelf=False):
    # Load line TASK_DEF = TASK TASK_NAME (GEN_TYPE_DECL)? (DECL_ARG_LIST)? RARROW RETURN_TYPE
    # TASK_DECL = TASK_DEF COLON
    # TASK_NAME = ID
    # TASK_STMT = (DECLARE_DECL BASE_DECL_STMT)? LOGIC_DECLARE TASK_LOGIC_STMT
    
    base = 'TASK'
    self.verify('TASK',True)
    taskDict = dict()
    
    taskDict['name'] = self.getValue()
    self.verify('ID')
    
    # See if trait has generic types
    if (self.check('LT')):
      taskDict['generics'] = self.loadGenTypeDecl()
    else:
      taskDict['generics'] = []
    
    #Load function arguments
    taskDict['params'] = self.loadDeclArgList(includeSelf)
    
    # Load return type
    self.verify('RARROW')
    taskDict['returnType'] = self.loadReturnType(includeSelf)
      
    if self.check('COLON'):
      self.verify('COLON')
      taskDict['taskDef'] = False
    else:
      taskDict['taskDef'] = True
      return BaseAST(base, [], taskDict)
    
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    # Check if declare block exists
    taskDict['declareBlock'] = None
    if (self.check('DECLARE')):
      #Next load signal definitions
      taskDict['declareBlock'] = self.loadDeclareBlock()
    
    #Next load logic
    taskDict['logicBlock'] = self.loadLogicBlock('task')
      
    #Return to original scope
    self.rmScope()
      
    return BaseAST(base, comment, taskDict)
    
  def loadReturnType(self, includeSelf):
    # RETURN_TYPE = (LPAREN GEN_TYPE (COMMA GEN_TYPE)* RPAREN) | TYPE_NAME
    if self.check('LPAREN'):
      self.verify('LPAREN')
      
      # Load types
      genNodes = []
      genNodes.append(self.loadGenType(includeSelf))
      while (self.check('COMMA')):
        self.verify('COMMA')
        genNodes.append(self.loadGenType(includeSelf))
        
      self.verify('RPAREN')
      
    else:
      # Load types
      genNodes = []
      genNodes.append(self.loadBaseName('TYPE', includeSelf)) # Yes
      
    return genNodes
    
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
    
  def loadDeclArgList(self, includeSelf=False):
    # Load line (LPAREN (DECL_ARG (COMMA DECL_ARG)*)? RPAREN)
    self.verify('LPAREN')
    
    argNodes = []
    # Does not require inputs
    if (self.check('RPAREN')):
      self.verify('RPAREN')
      return argNodes
    
    # Load vars
    argNodes.append(self.loadDeclArg(includeSelf))
    while (self.check('COMMA')):
      self.verify('COMMA')
      argNodes.append(self.loadDeclArg())
      
    self.verify('RPAREN')
    return argNodes
    
  def loadDeclArg(self, includeSelf=False):
    #Load line (TYPE_NAME GEN_TYPE_DECL? (STAR)* (ID|SELFVALUE) (ASSIGN CPLX_EXPR)?)
    # TYPE_NAME = ((ID (DOT ID)*) | SELFTYPE)
    # Define variable
    varType = dict()
    varType['type'] = self.loadBaseName('TYPE', includeSelf)
    # See if module has generic types
    if (self.check('LT')):
      varType['generics'] = self.loadGenTypeDecl()
    else:
      varType['generics'] = []
    
    #Determine number of dimensions
    dim = 0
    while (self.check('STAR')):
      dim += 1
      self.verify('STAR')
      
    varType['dim'] = dim
    
    #Get name
    varType['name'] = self.getValue()
    name = ['ID']
    if (includeSelf):
      name.append('SELFVALUE')
    self.verify(name)
    
    #See if default values are set
    varType['value'] = None
    if (self.check('ASSIGN')):
      self.verify('ASSIGN')
      
      #Get default value
      varType['value'] = self.loadComplexExpr(True)
    
    return BaseAST('PARAM', [], varType)
    
  def loadGenTypeDecl(self):
    # GEN_TYPE_DECL = LT GENERIC_TYPE (COMMA GENERIC_TYPE)* GT
    self.verify('LT')
    
    # Load types
    genNodes = []
    genNodes.append(self.loadGenericType())
    while (self.check('COMMA')):
      self.verify('COMMA')
      genNodes.append(self.loadGenericType())
      
    self.verify('GT')
    return genNodes
    
  def loadGenericType(self):
    # GENERIC_TYPE = (ID | SELFTYPE) (TYPE_BOUND)? (ASSIGN TYPE_NAME)?
    genDict = dict()
    
    # Load generic type name
    genDict['name'] = self.getValue()
    self.verify(['ID','SELFTYPE'])
    
    # Are there type bounds?
    if (self.check('LPAREN')):
      genDict['typeBound'] = self.loadTypeBound()
    else:
      genDict['typeBound'] = []
      
    # Is there a default type?
    if (self.check('ASSIGN')):
      self.verify('ASSIGN')
      genDict['defaultType'] = self.loadBaseName('TYPE')
    else:
      genDict['defaultType'] = None
      
    #Create module node
    return BaseAST(base, [], genDict)
    
  def loadTypeBound(self):
    # TYPE_BOUNDS = LPAREN ID (ADD_OPER ID)* RPAREN
    self.verify('LPAREN')
    
    # Get first bound
    bounds = [self.getValue()]
    self.verify('ID')
    
    # Determine if ther are more bounds
    if self.check('ADD_OPER'):
      self.verify('ADD_OPER')
      bounds.append(self.getValue())
      self.verify('ID')
    
    self.verify('RPAREN')
    
    return bounds
    
  def loadGenTypeCall(self, includeSelf=False):
    # GEN_TYPE_CALL = LT GEN_TYPE (COMMA GEN_TYPE)* GT
    # TYPE_NAME = ID (DOT ID)*
    
    self.verify('LT')
    
    # Load types
    genNodes = []
    genNodes.append(self.loadGenType(includeSelf))
    while (self.check('COMMA')):
      self.verify('COMMA')
      genNodes.append(self.loadGenType(includeSelf))
      
    self.verify('GT')
    return genNodes
    
  def loadGenType(self, includeSelf=False):
    #Load line (TYPE_NAME GEN_TYPE_DECL? (STAR)*)
    # TYPE_NAME = ((ID (DOT ID)*) | SELFTYPE)
    
    # Define variable
    varType = dict()
    varType['type'] = self.loadBaseName('TYPE', includeSelf)
    # See if module has generic types
    if (self.check('LT')):
      varType['generics'] = self.loadGenTypeDecl()
    else:
      varType['generics'] = []
    
    #Determine number of dimensions
    dim = 0
    while (self.check('STAR')):
      dim += 1
      self.verify('STAR')
      
    varType['dim'] = dim
    
    return BaseAST('TYPE', [], varType)
      
  def loadModuleDecl(self):
    # Read module line (MODULE ID GEN_TYPE_DECL? (LPAREN BLACKBOX RPAREN)? COLON)
    base = self.getType()
    self.verify('MODULE', True)
    modDict = dict()
    modDict['name'] = self.getValue()
    self.verify('ID')
    
    # See if module has generic types
    if (self.check('LT')):
      modDict['generics'] = self.loadGenTypeDecl()
    else:
      modDict['generics'] = []
    
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
      # Verify scope
      self.checkScope()
      
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
      # Verify scope
      self.checkScope()
      
      # Create port declaration
      portVars.append(self.loadVarDecl('port'))
      
    #Return to original scope
    self.rmScope()
      
    return portVars
    
  def loadArchDecl(self):
    # Get arch scope
    # Load line (ARCH ID GEN_TYPE_CALL? FOR ID GEN_TYPE_CALL? COLON)
    base = self.getType()
    self.verify('ARCH', True)
    archDict = dict()
    archDict['name'] = self.getValue()
    self.verify('ID')
    
    # See if architecture has generic types
    if (self.check('LT')):
      archDict['archGenerics'] = self.loadGenTypeDecl()
    
    self.verify('FOR')
    archDict['module'] = self.getValue()
    self.verify('ID')
    
    # See if module has generic types
    if (self.check('LT')):
      archDict['modGenerics'] = self.loadGenTypeCall()
    
    self.verify('COLON')
    comment = self.skip()
    
    # Add scope
    self.addScope()
    
    # Check if declare block exists
    archDict['declareBlock'] = None
    if (self.check('DECLARE')):
      #Next load signal definitions
      archDict['declareBlock'] = self.loadDeclareBlock()
    
    #Next load logic
    archDict['logicBlock'] = self.loadLogicBlock('arch')
    
    #Return to original scope
    self.rmScope()
    
    return BaseAST(base, comment, archDict)
    
  def loadArchStatements(self):
    # Load logic statements
    # (ASSIGNMENT|METHOD_TASK_CALL|FOR|CASE|IF|MODULE_INST|SPRO|APRO|PRO|ASSERTION|RENAME_CALL)
    statementNodes = []
    tokenList = ['ID', 'FOR', 'IF', 'CASE', 'SPRO', 'APRO', 'PRO', 'ASSERT', 'RENAME', 'LPAREN']
    while (self.check(tokenList,True)):
      # Load all statements
      statementNodes.append(self.loadStatement())
    
    return statementNodes
    
  def loadFuncStatements(self):
    # Load function statements
    # (ASSIGNMENT|METHOD_TASK_CALL|FOR|CASE|IF|ASSERTION|REPORT|RETURN)
    statementNodes = []
    tokenList = ['ID', 'FOR', 'IF', 'CASE', 'ASSERT', 'REPORT', 'RETURN', 'LPAREN', 'SELFVALUE']
    while (self.check(tokenList,True)):
      # Load all statements
      statementNodes.append(self.loadStatement())
    
    return statementNodes
    
  def loadTaskStatements(self):
    # Load task statements
    # (ASSIGNMENT | METHOD_TASK_CALL | FORBLOCK | CASEBLOCK | IFBLOCK | ASSERTION | PROBLOCK | MODULE_INST | RETURN_STMT)
    statementNodes = []
    tokenList = ['ID', 'FOR', 'IF', 'CASE', 'SPRO', 'APRO', 'PRO', 'ASSERT', 'REPORT', 'RETURN', 'LPAREN', 'SELFVALUE']
    while (self.check(tokenList,True)):
      # Load all statements
      statementNodes.append(self.loadStatement())
    
    return statementNodes
    
  def loadStatement(self, isPro=False):
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
      
    elif (self.check('LPAREN')):
      return self.loadAssignment()
      
    elif (self.check(['ID', 'SELFVALUE'])):
      # If ID, determine if its a module inst., var declaration, or assignment
      type = self.determineStatement()
      if (type == 'MODULE'):
        return self.loadModuleInst()
        
      elif (type == 'METHOD_TASK'):
        return self.loadVarDecl('signal')
        
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
    #    Look for (ID ID) pattern
    # FUNC_METHOD_CALL = ID (INDEX_LIST)? (DOT ID (INDEX_LIST)?)* (DOT FUNC_CALL)
    # ASSIGNMENT = (VAR | TUPLE_EXPR) ASSIGN_OPTIONS CMPX_EXPR
    
    ind = 0
    token1 = self.token
    token2 = self.peek(ind)
    
    asgnList = ['ASSIGN', 'CMPD_ARITH_ASSIGN', 'CMPD_LOGICAL_ASSIGN', 'POST_OPER']
    
    # See what next ID is
    if ((token1.type == 'ID') and (token2.type == 'ID')):
      # Both ID, its a module
      return 'MODULE'

    else:
      # Check entire line until EOL to check for assignments
      while (self.peek(ind).type is not 'EOL'):
        if (self.peek(ind).type in asgnList):
          return 'ASSIGNMENT'
        ind += 1
          
      # No assignment, so its a task or method call
      return 'METHOD_TASK'
    
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
    
    return BaseAST(base, comment, elifDict)
    
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
    # Load line ((VAR | TUPLE_EXPR) ASSIGN_OPTIONS CMPX_EXPR)
    # OPER = (ASSIGN|CMPD_ARITH_ASSIGN|CMPD_LOGICAL_ASSIGN|POST_OPER)
    asgnDict = dict()
    if (self.check('LPAREN')):
      asgnDict['leftVar'] = self.loadCallArgList(False)
    else:
      asgnDict['leftVar'] = self.loadVar(False)
      
    # Determine assignment type
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
    # Load line (ID BASE_NAME GEN_TYPE_CALL? (LPAREN (ID | BLACKBOX) RPAREN)? COLON)
    # BASE_NAME = ID (DOT ID)*
    base = 'MODULE_INST'
    modDict = dict()
    modDict['name'] = self.getValue()
    self.verify('ID')
    modDict['module'] = self.loadBaseName('NAME')
    
    # See if module has generic types
    if (self.check('LT')):
      modDict['generics'] = self.loadGenTypeCall()
    else:
      modDict['generics'] = []
    
    # Determine if specific architecture is called
    if (self.check('LPAREN')):
      self.verify('LPAREN')
      modDict['arch'] = self.getValue()
      self.verify(['ID','BLACKBOX'])
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
    
    return BaseAST(base, comment, modDict)
    
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
        self.verify('COMMA')
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
  # this variable will be passed to semantic analyzer to verify
  # array sizes are constant values. assignment array sizes can be 
  # constant or signal
  def loadComplexExpr(self,isDecl):
    # Load (AGGREGATE | SIMP_EXPR)
    if (self.check('LBRACK')):
      return self.loadAggregate(isDecl)
    else:
      return self.loadSimpleExpr(isDecl)
    
  def loadAggregate(self,isDecl):
    # Load line (LCURBRAC ELEM_ASSOC (COMMA ELEM_ASSOC)* RCURBRAC)
    comments = []
    self.verify('LBRACK')
    comments += self.skip()
    elem = [self.loadElemAssoc(isDecl)]
    while (self.check('COMMA')):
      self.verify('COMMA')
      comments += self.skip()
      elem.append(self.loadElemAssoc(isDecl))
      comments += self.skip()
      
    self.verify('RBRACK')
    
    aggDict = dict()
    aggDict['elem'] = elem
    
    return BaseAST('AGGREGATE', comments, aggDict)
    
  def loadElemAssoc(self,isDecl):
    # Load ((CHOICES ASSIGN)? (AGGREGATE|SIMP_EXPR))
    elemDict = dict()
    
    # Determine if another aggregate is next, CHOICES 
    if (self.check('LBRACK')):
      elemDict['left'] = None
      elemDict['right'] = self.loadAggregate(isDecl)
      return BaseAST('ELEM', [], elemDict)
    
    # At this point, not sure if its choice or value
    values = self.loadChoices(isDecl)
    
    # Check if ASSIGN exists, if then values is the index 
    # and the values need to be loaded
    if (self.check('ASSIGN')):
      self.verify('ASSIGN')
      elemDict['left'] = values
      
      if (self.check('LBRACK')):
        elemDict['right'] = self.loadAggregate(isDecl)
      else:
        elemDict['right'] = self.loadSimpleExpr(isDecl)
    else:
      elemDict['left'] = None
      elemDict['right'] = values
    
    return BaseAST('ELEM', [], elemDict)
    
  def loadChoices(self,isDecl):
    # Load CHOICE (OR_BAR CHOICE)*
    args = []
    args.append(self.loadChoice(isDecl))
    while (self.check('OR_BAR')):
      self.verify('OR_BAR')
      self.skip()
      args.append(self.loadChoice(isDecl))
      self.skip()
    
    return args
  
  def loadChoice(self,isDecl):
    # Load (SLICE | OTHERS)
    if (self.check('OTHERS')):
      arg = BaseAST('OTHERS', [], dict())
      self.verify('OTHERS')
    else:
      arg = self.loadIndex(isDecl)
        
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
    # Load (TERM (RELATION_OPER TERM)*)
    node = self.loadTerm(isDecl)
    
    oper = ['RELATION_OPER']
    while (self.check(oper)):
      # Create new expr node
      exprDict = dict()
      exprDict['op']   = self.getValue()
      self.verify(oper)
      exprDict['params'] = [node, self.loadTerm(isDecl)]
      node = BaseAST('EXPR', [], exprDict)
      
    return node
    
  def loadTerm(self,isDecl):
    # Load (FACT ((ADD_OPER | SUB_OPER | CAT) FACT)*)
    node = self.loadFactor(isDecl)
    
    oper = ['ADD_OPER', 'SUB_OPER', 'CAT']
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
    # Load ((ADD_OPER | SUB_OPER | NOT_OPER)? PRIMARY)
    exprDict = dict()
    
    oper = ['ADD_OPER', 'SUB_OPER', 'NOT_OPER']
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
    funcList  = ['ID', 'LOGICAL_OPER', 'MOD_REM_OPER', 'NOT_OPER']
    if (self.check(constList)):
      return self.loadConst(isDecl)
      
    elif (self.check('LPAREN')):
      self.verify('LPAREN')
      expr = self.loadSimpleExpr(isDecl)
      self.verify('RPAREN')
      return expr
      
    elif (self.check(funcList)):
      # We dont know if it is function or variable
      if (self.peek().type in ['LPAREN','LT']):
        return self.loadFuncCall(isDecl)
      else:
        return self.loadVar(isDecl)
        
    elif (self.check('SELFVALUE')):
      return self.loadVar(isDecl,includeSelf=True)
      
    else:
      self.error()
    
  def loadFuncCall(self, isDecl):
    # Load (FUNC_NAME GEN_TYPE_CALL? CALL_ARG_LIST)
    funcList  = ['ID', 'LOGICAL_OPER', 'MOD_REM_OPER', 'NOT_OPER']
    funcDict = {'name': self.getValue()}
    self.verify(funcList)
    
    # See if module has generic types
    if (self.check('LT')):
      funcDict['generics'] = self.loadGenTypeCall()
    else:
      funcDict['generics'] = []
    
    # Input parameters
    funcDict['params'] = self.loadCallArgList(isDecl)
    
    return BaseAST('FUNCCALL', [], funcDict)
      
  def loadConst(self, isDecl):
    # CONST = (INTEGER | FLOAT | BIT_INIT_HEX | BIT_INIT_BIN | STRING | BOOLEAN)
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
    
  def loadVar(self, isDecl, includeSelf=False):
    #Load (ID (INDEX_LIST)? (DOT VAR)? ) 
    varDict = dict()
    varDict['name'] = self.getValue()
    tokenList = ['ID']
    if (includeSelf):
      tokenList.append('SELFVALUE')
    self.verify(tokenList)
    
    varDict['decl'] = isDecl
    
    # check slice
    if (self.check('LBRACK')):
      varDict['array'] = self.loadIndexList(isDecl)
    else:
      varDict['array'] = None
      
    # check for struct or interface variable
    funcList  = ['ID', 'LOGICAL_OPER', 'MOD_REM_OPER', 'NOT_OPER']
    if (self.check('DOT')):
      self.verify('DOT')
      if (self.check(funcList) and (self.peek().type in ['LPAREN','LT'])):
        # Load method
        varDict['field'] = None
        varDict['method']  = self.loadFuncCall(isDecl)
      elif (self.check('ID')):
        # Recursively load fields
        varDict['field'] = self.loadVar(isDecl)
        varDict['method']  = None
      
    else:
      varDict['field'] = None
      varDict['method']  = None
      
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
      
  def loadBaseName(self, baseName, includeSelf=False):
    # TYPE_NAME = ID (DOT ID)*
    genType = dict()
    genType['name'] = [self.getValue()]
    
    # If SELF, only thing. Else it could be concrete type
    if (self.check('ID')):
      self.verify('ID')
        
      # Check if DOT is used to only load one item
      while (self.check('DOT')):
        self.verify('DOT')
        genType['name'].append(self.getValue())
        self.verify('ID')
        
    elif (self.check('SELFTYPE')):
      self.verify('SELFTYPE')
      
    return BaseAST(baseName, [], genType)
      
