class BaseType (object):
  def __init__(self,name,symbol):
    self.name   = name
    self.symbol = symbol
    
  def __str__(self):
    tmpDict = self.__dict__
    tmpDict.pop('name')
    tmpDict.pop('symbol')
    string = '{0}: {1}\n'.format(self.symbol, self.name)
    for attr,val in tmpDict:
      if val is list:
        string += '  {0}:\n'.format(attr)
        for ind in val:
          string += '    {0}:\n'.format(ind)
      else:
        string += '  {0}: {1}\n'.format(attr,val)
    return string

class BuiltinType (BaseType):
  def __init__(self, configDict):
    # Define type from dict
    self.symbol = 'builtin'
    for var, val in configDict.iteritems():
      setattr(self, var, val)
      
    # Required type attributes
    requiredAttr = ['name','minArgs','maxArgs','numArgs','argTypes','tokens']
    for check in requiredAttr:
      if not hasattr(self,check):
        print('Error: Type missing "{0}" attr'.format(check))
        
class StructType (BaseType):
  def __init__(self,name=None,fields=[]):
    BaseType.__init__(name,'struct')
    self.fields = fields
    
class InterfaceType (BaseType):
  def __init__(self,name=None,fields=[]):
    BaseType.__init__(name,'interface')
    self.fields = fields
    
class EnumType (BaseType):
  def __init__(self,name=None,states=[]):
    BaseType.__init__(name,'enum')
    self.states = states
    
class ModuleType (BaseType):
  def __init__(self,name=None,arch=None,gens=[],ports=[]):
    BaseType.__init__(name,'module')
    self.arch  = arch
    self.gens  = gens
    self.ports = ports
        
class VarSymbol (object):
  def __init__(self,name=None,type=None,const=None,array=None,value=None):
    Symbol.__init__('var')
    self.name  = name
    self.type  = type
    self.const = const
    self.array = array
    self.value = value
  
  def __str__(self):
    return '{0} {1} {2} {3} {4}'.format(self.name, self.type, self.const, self.array, self.value)
    
class MethodSymbol (object):
  def __init__(self,name=None):
    self.name   = name
    self.inputNames = inputNames
    self.inputTypes = inputTypes
    self.outputNames = outputNames
    self.outputTypes = outputTypes
      
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
    if (self._types.has_key(typeSymbol.name)):
      self._types[typeSymbol.name] = typeSymbol
    else:
      raise 'Trying to insert type "{0}", but type already exists'.format(typeSymbol.name)
    
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
      raise Exception('Variable "{0}" not found'.format(node.name))
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
      typeStr = '{0}{1}'.format(val.name.ljust(typeWidth,' '), val.tokens.ljust(typeWidth,' '))
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
