from collections import OrderedDict
from copy import deepcopy

def arraySize(array):
  # At this point, all constant variables have been
  # replaced by their integer, but not signals. This 
  # code is to verify signal INDEXING, not signal slicing.
  # If any index is a signal, the other index must be the
  # same signal.
  indStr = [isinstance(m,str) for m in array]
  bothSame = (array[0] == array[1])
  if (all(indStr) and bothSame):
    return (None, None, 1)
  elif (all(indStr) and not(bothSame)):
    raise Exception('Variable index slicing')
  elif (any(indStr)):
    raise Exception('Variable index slicing')
  
  
  # Assuming indices are numbers
  if (array[0] > array[1]):
    return (array[0], array[1], (array[0] - array[1] + 1))
  else:
    return (array[1], array[0], (array[1] - array[0] + 1))

class NodeVisitor (object):
  def visit(self, node):
    methodname = 'visit_' + node.base.lower()
    visitor = getattr(self, methodname, self.visit_error)
    return visitor(node)
    
  def visit_error(self, node):
    print('Visit Error: No visitor for type "{0}"'.format(node.base))
    
# Creates type class from dict, and verifies attributes
class TypeSymbol (object):
  def __init__(self, configDict):
    # Define type from dict
    for var, val in configDict.iteritems():
      setattr(self, var, val)
      
    # Required type attributes
    requiredAttr = ['name','minArgs','maxArgs','numArgs','argTypes','tokens']
    for check in requiredAttr:
      if not hasattr(self,check):
        print('Error: Type missing "{0}" attr'.format(check))
        
class VarSymbol (object):
  def __init__(self,name=None,type=None,const=None,array=None,value=None):
    self.name  = name
    self.type  = type
    self.const = const
    self.array = array
    self.value = value
  
  def __str__(self):
    return '{0} {1} {2} {3} {4}'.format(self.name,self.type,self.const,self.array,self.value)
      
class ScopedSymbolTable (object):
  def __init__(self,builtin_types,scopeName,scopeLevel,enclosingScope=None):
    self._types         = OrderedDict()
    self._variables     = OrderedDict()
    self.scopeName      = scopeName
    self.scopeLevel     = scopeLevel
    self.enclosingScope = enclosingScope
    
    for i in builtin_types:
      self.insertType(TypeSymbol(i))
      
  def insertType(self, typeSymbol):
    print('Table: Adding type "{0}"'.format(typeSymbol.name))
    self._types[typeSymbol.name] = typeSymbol
    
  def addVariable(self, node, typeConfig, initVal, currentScopeOnly=False):
    print('Lookup Type: "{0}"'.format(node.type))
    symbol = self._types.get(node.type)
    
    if (symbol is None):
      if (currentScopeOnly):
        # If only the scope, fail
        return False
      else:
        # TODO: Recusively look for scope
        return False
    
    # Good so far, check type arguments
    configType = self.checkTypeConfig(node, typeConfig)
    
    if not configType:
      print('Config invalid')
      return False
      
    initValid = self.checkInitValue(node, initVal)
    
    # Check initial value
    if not initValid:
      print('Init invalid')
      return False
      
    # Add variable to table
    self.insertVar(node,initVal)
    
    return True
    
  def checkTypeConfig(self, node, configTypes):
    # Get symbols
    symbol = self._types.get(node.type)
    
    # Check number of args
    typeConfig = node.typeConfig
    minArgs = symbol.minArgs
    maxArgs = symbol.maxArgs
    lenArgs = len(typeConfig)
    if (lenArgs < minArgs):
      print('Variable "{0}" type "{1}" needs minimum of {2}'.format(node.name, node.type, minArgs))
      raise Exception('Type min args')
      
    if (lenArgs > maxArgs):
      print('Variable "{0}" type "{1}" over maximum of {2}'.format(node.name, node.type, maxArgs))
      raise Exception('Type max args')
      
    # Check arguments types match
    argInd = symbol.numArgs.index(lenArgs)
    argTypes = symbol.argTypes[argInd]
    if (len(configTypes) > 0):
      for ind,arg in enumerate(configTypes):
        if (argTypes[ind] != arg):
          print('Oh no')
          raise Exception('Type config arg wrong')
          
    return True
    
  def checkInitValue(self, varNode, initValue):
    # No init value, skip
    if initValue.value is None:
      return True
      
    # Determine array size
    size = [arraySize(ind)[2] for ind in varNode.array]
    for dim in size:
      if (dim != len(initValue.value)):
        return False
        
    return True
  
  def insertVar(self, varNode, varSymbol):
    if (self._variables.has_key(varNode.name)):
      raise Exception('Multiple variables with name "{0}"'.format(varNode.name))
      
    print('Table: Adding variable "{0}"'.format(varNode.name))
    self._variables[varNode.name] = varNode
    self._variables[varNode.name].value = varSymbol.value
    
  def lookupVar(self, node):
    print('Lookup variable "{0}"'.format(node.name))
    declNode = self._variables.get(node.name)
    
    if (declNode is not None):
      # See if there is indexing
      varIndex = self.checkIndicies(declNode,node)
      if (varIndex is None):
        return None
      else:
        rtrnNode = deepcopy(declNode)
        rtrnNode.array = varIndex

        return rtrnNode
    else:
      # Not found
      return None
      
  def checkIndicies(self,declNode,node):
    # No index in refNode, use declNode array
    if (node.array == [None]):
      return deepcopy(declNode.array)
    
    # See if declaration is array
    lenRef = len(node.array)-1
    for ind,dim in enumerate(declNode.array):
      if (ind <= lenRef):
        # Dimension exists, check values of array
        decDim = arraySize(dim)
        refDim = arraySize(node.array[ind])
        if ((refDim[0] > decDim[0]) or (refDim[1] < decDim[1])):
          return None
        
      else:
        return None
        
    return deepcopy(node.array)
    
  def status(self):
    # Plot header
    header = '|{0}|'.format('Scope Symbol Table'.center(50,' '))
    width = len(header)
    typeWidth = (width-2)/2
    lines = ['=' * width, header, '=' * width]
    
    # Plot types
    lines.append('|{0}|'.format('Types'.center(width-2,' ')))
    lines.append('-'*width)
    lines.append('|{0}{1}|'.format('Name'.ljust(typeWidth,' '),'Tokens'.ljust(typeWidth,' ')))
    lines.append('-'*width)
    for var,val in self._types.iteritems():
      typeStr = '{0}{1}'.format(val.name.ljust(typeWidth,' '),val.tokens.ljust(typeWidth,' '))
      lines.append('|{0}|'.format(typeStr))
    
    # Plot variables
    lines.append('-'*width)
    lines.append('|{0}|'.format('Variables'.center(width-2,' ')))
    lines.append('-'*width)
    varWidth = (width-2)/5
    nameStr = 'Name'.ljust(varWidth,' ')
    constStr = 'Const'.ljust(varWidth,' ')
    typeStr = 'Type'.ljust(varWidth,' ')
    valStr = 'Init.'.ljust(varWidth,' ')
    arrayStr = 'Array'.ljust(varWidth,' ')
    lines.append('|{0}{1}{2}{3}{4}|'.format(nameStr,constStr,typeStr,valStr,arrayStr))
    lines.append('-'*width)
    for var,val in self._variables.iteritems():
      nameStr = val.name.ljust(varWidth,' ')
      constStr = str(val.const).ljust(varWidth,' ')
      typeStr = val.type.ljust(varWidth,' ')
      valStr = str(val.value).ljust(varWidth,' ')
      arrayStr = str(val.array).ljust(varWidth,' ')
      typeStr = '{0}{1}{2}{3}{4}'.format(nameStr,constStr,typeStr,valStr,arrayStr)
      lines.append('|{0}|'.format(typeStr))
      
    lines.append('-'*width)
    print('\n'.join(lines))
    
# Perform deeper analysis of AST
# Check if variables exist
# Check if types are defined
# Check indexing and slicing has constant variables
# Check array sizes match
# Check scopes match
class SemanticAnalyzer (NodeVisitor):
  def __init__(self,builtin_types):
    self.scope = ScopedSymbolTable(builtin_types,'global',1,None)
    
  def visit_file(self,node):
    
    # TODO: import
    for ind in node.importNodes:
      self.visit(ind)
    
    # Module
    self.visit(node.moduleNode)
    
  def visit_module(self,node):
    # Check generic declarations
    for gen in node.genDeclNodes:
      self.visit(gen)
      
    for port in node.portDeclNodes:
      self.visit(port)
      
    self.visit(node.archNode)
    
  def visit_archblock(self, node):
    # Loop over signal declarations
    for sig in node.sigDeclNodes:
      self.visit(sig)
      
    self.scope.status()
      
    # Loop through statements
    for sm in node.statements:
      self.visit(sm)
    
      
  def visit_decl(self,node):
    # Check declarations
    # Determine config arg types
    typeConfigTypes = []
    for arg in node.typeConfig:
      argSym = self.visit(arg)
      
      # Variables must be constant
      if (argSym.const):
        typeConfigTypes.append(argSym.type)
      else:
        print(':,(')
        raise Exception('TypeConfig bad')
       
    # Replace array indicies with values 
    self.checkArray(node)
          
    # Validate Init value
    if (node.value != [None]):
      # No interface port can have value
      if (node.port is None):
        initVal = self.visit(node.value)
      else:
        print('Ports can not have init value')
        raise Exception('Port Init')
    else:
      initVal = VarSymbol()
    
    # Verify Type and TypeConfig valid
    varAdded  = self.scope.addVariable(node,typeConfigTypes,initVal)
    
    if not varAdded:
      raise Exception('Var Decl Invalid')
      
  def visit_syncpro(self, node):
    # Verify args
    argList = node.args
    if (len(argList) != 2):
      raise Exception('spro too many args')
      
    # Verify args
    for arg in argList:
      varSym = self.visit(arg)
      if (varSym is not None):
        typeValid  = (varSym.type == 'bit')
        sizeList = [arraySize(d)[2] for d in varSym.array]
        arrayValid = (sizeList == [1])
        constValid = (varSym.const == False)
        if not(typeValid and arrayValid and constValid):
          raise Exception('spro args {0} not valid arguement'.format(varSym.name))
      else:
        raise Exception('spro args {0} not found'.format(varSym.name))
        
    # Loop statements
    for stmt in node.statements:
      self.visit(stmt)
      
  def visit_assignment(self,node):
    leftVar = self.visit(node.leftVar)
    
    rightExpr = self.visit(node.rightExpr)
      
  def visit_expr(self,node):
    # First visit node to verify it
    # Validate 'left'
    leftValid = self.visit(node.left)
    
    # See if 'op' and 'right' exist
    if hasattr(node,'op'):
      #Something
      pass
      
    return leftValid
    
  def visit_term(self,node):
    # First visit node to verify it
    # Validate 'left'
    leftValid = self.visit(node.left)
    
    # See if 'op' and 'right' exist
    if hasattr(node,'op'):
      #Something
      pass
    
    return leftValid
      
  def visit_factor(self,node):
    # Validate
    return self.visit(node)
    
  def visit_num(self, node):
    # Number, return values
    return VarSymbol(None,node.type,node.const,node.array,node.value)
    
  def visit_var(self, node):
    # Replace array indicies with values 
    self.checkArray(node)
    
    declNode = self.scope.lookupVar(node)
    if (declNode is None):
      return VarSymbol(False,False,False,False,False)
    else: 
      return VarSymbol(node.name,declNode.type, declNode.const,declNode.array,declNode.value) 
      
  def checkArray(self,node):
    if (node.array == [None]):
      return
      
    # If var is a declaration, array values must be const
    isDecl = node.decl
    
    # Check array sizes use constants
    arrayVal = node.array
    for i,arg in enumerate(node.array):
      for j,val in enumerate(arg):
        if (val is 0):
          continue
        
        # Visit expr
        varSym = self.visit(val)
        
        # Variables must be integer
        typeValid = varSym.type in ['INTEGER','sint','uint']
        
        # Truth table to error when isDecl and varSym is not const
        constValid = not(isDecl) or varSym.const
        
        if (constValid and typeValid):
          # If value is none, just give name
          if (varSym.value is None):
            arrayVal[i][j] = varSym.name
          else:
            arrayVal[i][j] = varSym.value[0]
          
        else:
          raise Exception('ArrayInd bad')
          
