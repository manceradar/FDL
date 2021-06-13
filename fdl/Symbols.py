from copy import deepcopy
from .SymbolTable import SymbolTable
import numpy as np

def flip(m,axis):
  if not hasattr(m, 'ndim'):
    m = asarray(m)
  indexer = [slice(None)] * m.ndim
  try:
    indexer[axis] = slice(None, None, -1)
  except IndexError:
    raise ValueError("axis=%i is invalid for the %i-dimensional input array"
                       % (axis, m.ndim))
  return m[tuple(indexer)]

def determineDim(array):
  # Determine dimensions of input parameter
  numDim = 0
  for dim in array:
    # loop over dimensions
    if (dim[0] != dim[1]):
      numDim += 1
      
  return numDim
  
def calcOverloadFuncName(funcName, inputs):
  # Determine function name with one that can be resolved
  for x in inputs:
    funcName += '_{0}{1}'.format(x.typeName, x.typeDim)
    
  return funcName
  
def calcAllFuncNames(funcName, inputs):
  # Determine all function names for function
  
  # Calculate name with no inputs
  defaultInd = np.array([x.value == None for x in inputs])
  if (len(inputs) == 0):
    defaultParam = inputs
  else:
    defaultParam = list(np.array(inputs)[defaultInd])
    
  names = [calcOverloadFuncName(funcName, defaultParam)]
  
  for ind in range(0,len(inputs)):
    if (inputs[ind].value != None):
      name = calcOverloadFuncName(funcName, inputs[0:ind+1])
      names.append(name)
    
  return names

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
    return (array[1], array[0], (array[0] - array[1] + 1))
  else:
    return (array[0], array[1], (array[1] - array[0] + 1))

# All symbols inherit from base symbol
class BaseSymbol (object):
  def __init__(self,name,type,ast=None):
    self.name        = name
    self.type        = type
    self.ast         = deepcopy(ast)
    # Will be replaced, have limited values compared to signals
    self._parameter  = False
    # Symbol imported, only necessary for debug
    self._imported   = False
    # Symbol was referenced in code, anywhere
    self._referenced = False
    
  def isParameter(self):
    return self._parameter
    
  def setParameter(self):
    self._parameter = True

  def isImported(self):
    return self._imported
    
  def setImported(self):
    self._imported = True
    
  def isReferenced(self):
    return self._referenced
    
  def gotReferenced(self):
    self._referenced = True
    
  def rmReferenced(self):
    self._referenced = False
    
  def getAST(self):
    return self.ast
    
  def getName(self):
    return self.__class__.__name__
    
  def __str__(self):
    tmpDict = self.__dict__
    string = '{0}: {1}\n'.format(self.type, self.name)
    for attr,val in tmpDict.iteritems():
      if val is list:
        string += '  {0}:\n'.format(attr)
        for ind in val:
          string += '    {0}:\n'.format(ind)
      else:
        string += '  {0}: {1}\n'.format(attr,val)
    return string
    
# All symbols that have parameter inputs use this class to verify 
# inputs and declarations
class Params (object):
  def verifyParamDecl(self):
    # Param verification
    params = self.returnParams()
    self.required = [x.value == None for x in params]
    self.numArgs  = len(self.required)
    
    self.verifyDefaultValues()
    
  def verifyDefaultValues(self):
    # Default values can only be defined after previous values havent.
    # After default values defined, next params must have default values.
    valuesDef = False
    for paramReq in self.required:
      # Invalid
      if (paramReq and valuesDef):
        raise('Param input invalid')
      
      # Determine when values must be required
      if (not paramReq and not valuesDef):
        valuesDef = True
    
  def verifyInputs(self, paramNodes):
    # Check number of params
    lenArgs = len(paramNodes)
    
    if (lenArgs > self.numArgs):
      #Too many params
      raise('"{0}" has {1} params but {2} given.'.format(self.name, self.numArgs, lenArgs))
    
    # Loop over input params
    params = self.returnParams()
    
    inputValues = []
    for ind,node in enumerate(paramNodes):
      # Check params match
      if (node.typeName not in params[ind].typeName):
        raise Exception('{0}: {1} type does not match {2}.'.format(params[ind].name, node.typeName, params[ind].typeName))
        
      # Check dimensions
      if (node.typeDim != params[ind].typeDim):
        raise Exception('{0} dims does not match {1}.'.format(node.name, params[ind].name))
        
      # Append input
      inputValues.append((params[ind].name, deepcopy(node.value)))
      
    # Loop over parameters not defined, if they exist
    for ind in range(lenArgs,self.numArgs):
      inputValues.append((params[ind].name, params[ind].value))
          
    return inputValues
    
# Define symbols from builtin or user defined sources
class ParamSymbol (BaseSymbol):
  def __init__(self, node):
    BaseSymbol.__init__(self, node.name, 'signal', node)
    self.typeName    = node.type
    self.typeDim     = node.dim
    self.value       = node.value
    self.const       = False
    self.setParameter()
    
  # Used for simple indexing, before validating array is defined
  def verifySimpleIndex(self, index):
    # Determine type dimensions with given index. This is a quick check,
    # not validating if indices are out of range. We will do that on 
    # second path.
    numDim = self.typeDim
      
    if self.typeDim == 0:
      raise Exception('Bad indexing 1')
      
    # Check indexing
    for dim in index:
      # loop over dimensions
      if (len(dim) == 1):
        self.typeDim -= 1
        
    if self.typeDim < 0:
      raise Exception('Bad indexing 2')
      
    return
    
# Define builtin node from YAML config
class ParamNode (object):
  def __init__(self, configDict, ind):
    self.name   = configDict['paramName'][ind]
    self.type   = configDict['paramTypeName'][ind]
    self.dim    = configDict['paramTypeDim'][ind]
    self.value  = configDict['paramValue'][ind]
    
# Structures and interfaces use this class to add and find field variables
class Field (object):
  def __init__(self):
    # Load fields
    self.fields = []
    
  def addField(self, field):
    self.fields.append(field)
      
  def getField(self, name):
    # Find field
    for field in self.fields:
      if (field.name == name):
        return field
        
    # Field not found
    return None

# Define builtin type from YAML config
class BuiltinTypeSymbol (BaseSymbol, SymbolTable, Params):
  def __init__(self, configDict, scopeLevel, encScope):
    # Define type from dict
    BaseSymbol.__init__(self,configDict['name'],'type')
    SymbolTable.__init__(self, configDict['name'], scopeLevel, encScope)
    
    # Param insertion
    for ind in range(len(configDict['paramTypeName'])):
      node = ParamNode(configDict, ind)
      self.insert(ParamSymbol(node))
      
    self.verifyParamDecl()
    
# Define builtin process from YAML config
class ProcessSymbol (BaseSymbol, SymbolTable, Params):
  def __init__(self, configDict, scopeLevel, encScope):
    # Define type from dict
    BaseSymbol.__init__(self,configDict['name'],'process')
    SymbolTable.__init__(self, configDict['name'], scopeLevel, encScope)
    
    # Param insertion
    for ind in range(len(configDict['paramTypeName'])):
      node = ParamNode(configDict, ind)
      self.insert(ParamSymbol(node))
      
    self.verifyParamDecl()
        
# Define structure symbol for data consolidation
class StructSymbol (BaseSymbol, SymbolTable, Params, Field):
  def __init__(self, node, scopeLevel, encScope):
    BaseSymbol.__init__(self, node.name, 'type', node)
    SymbolTable.__init__(self, node.name, scopeLevel, encScope)
    Field.__init__(self)
    
# Define interface symbol for data consolidation
class InterfaceSymbol (BaseSymbol, SymbolTable, Params, Field):
  def __init__(self, node, scopeLevel, encScope):
    BaseSymbol.__init__(self, node.name, 'type', node)
    SymbolTable.__init__(self, node.name, scopeLevel, encScope)
    Field.__init__(self)    
    
# Define user defined function symbol
class FuncSymbol (BaseSymbol, SymbolTable, Params):
  def __init__(self, node, scopeLevel, encScope):
    if (type(node).__name__ == 'BaseAST'):
      self.__initClass__(node, scopeLevel, encScope)
    elif (type(node).__name__ == 'dict'):
      self.__initDict__(node, scopeLevel, encScope)
      
  def __initClass__(self, node, scopeLevel, encScope):
    BaseSymbol.__init__(self, node.name, 'function', node)
    SymbolTable.__init__(self, node.name, scopeLevel, encScope)
    self.synth = True
    self.returnTypeName = []
    self.returnTypeDim  = []
    
  def __initDict__(self, configDict, scopeLevel, encScope):
    # Define type from dict
    BaseSymbol.__init__(self,configDict['name'],'function')
    SymbolTable.__init__(self, configDict['name'], scopeLevel, encScope)
    self.synth = False
    self.returnTypeName = configDict['returnTypeName']
    self.returnTypeDim  = configDict['returnTypeDim']
    
    # Param insertion
    for ind in range(len(configDict['paramTypeName'])):
      node = ParamNode(configDict, ind)
      self.insert(ParamSymbol(node))
      
    self.verifyParamDecl()
    
# Define builtin attribute symbols from YAML config
class AttrSymbol (BaseSymbol, SymbolTable, Params):
  def __init__(self, configDict, scopeLevel, encScope):
    BaseSymbol.__init__(self, configDict['name'], 'attr')
    SymbolTable.__init__(self, configDict['name'], scopeLevel, encScope)
    self.returnTypeName = configDict['returnTypeName']
    self.returnTypeDim  = configDict['returnTypeDim']
    for ind in range(len(configDict['paramTypeName'])):
      node = ParamNode(configDict, ind)
      self.insert(ParamSymbol(node))
    
    self.verifyParamDecl()
    
class EnumSymbol (BaseSymbol):
  def __init__(self,name,states):
    BaseSymbol.__init__(name, 'type')
    self.states = states
    
class EnumStateSymbol (BaseSymbol):
  def __init__(self, name):
    BaseSymbol.__init__(name, 'state')
        
# 
class SignalSymbol (BaseSymbol):
  def __init__(self, node, inputParams):
    if (type(node).__name__ == 'BaseAST'):
      self.__initClass__(node)
    elif (type(node).__name__ == 'dict'):
      self.__initDict__(node)
      
    self.typeParams  = inputParams
    self.generic     = False
    self.port        = False
    
    # Array sizes TBD later
    self.flipInd       = None
    self.array         = None
    self.dimIndOffset  = None
    
    # Values
    self.value         = np.empty(1, dtype='O')
    self.initAsgnd     = np.full(1, False, dtype=bool)
    self.valAsgnd      = np.full(1, False, dtype=bool)
    
  def __initClass__(self, node):
    BaseSymbol.__init__(self, node.name, 'signal', node)
    self.typeName    = node.typeName
    if (node.base is 'CONST'):
      self.typeDim   = 0
    else:
      self.typeDim     = determineDim(node.array)
    self.const       = node.const
    self.portType    = node.port
    
  def __initDict__(self, node):
    BaseSymbol.__init__(self, node['name'], 'signal')
    self.typeName    = node['typeName']
    self.typeDim     = determineDim(node['array'])
    self.const       = node['const']
    self.portType    = node['port']
    
  def setGeneric(self):
    self.generic = True
    
  def isGeneric(self):
    return self.generic
    
  def setPort(self):
    self.port = True
    
  def isPort(self):
    return self.port
    
  # Used for simple indexing, before validating array is defined
  def verifySimpleIndex(self, index):
    # Determine type dimensions with given index. This is a quick check,
    # not validating if indices are out of range. We will do that on 
    # second path.
    numDim = self.typeDim
      
    if self.typeDim == 0:
      raise Exception('Bad indexing 1')
      
    # Check indexing
    for dim in index:
      # loop over dimensions
      if (len(dim) == 1):
        self.typeDim -= 1
        
    if self.typeDim < 0:
      raise Exception('Bad indexing 2')
      
    return
    
  def setArray(self, array):
    self.flipInd     = [x[0] > x[1] for x in array]
    self.array       = [list(arraySize(x)[0:2]) for x in array]
    
    arrayDim = tuple([arraySize(ind)[2] for ind in array])
    
    self.dimIndOffset  = [arraySize(ind)[0] for ind in array]
    
    self.value         = np.empty(arrayDim, dtype='O')
    self.initAsgnd     = np.full(arrayDim, False, dtype=bool)
    self.valAsgnd      = np.full(arrayDim, False, dtype=bool)
    
  def assignConstValue(self, value):
    self.value[[0,0]] = value
    self.initAsgnd[[0,0]] = True
    self.valAsgnd[[0,0]] = True
    
  def assignInitValue(self, node, index=None):
    # Verify type
    if (node.typeName != self.typeName):
      raise Exception('Init Variable Type Mismatch')
    
    if (index is None):
      index = deepcopy(self.array)
      
      # Get indexing in right frame
      print(index)
      index = [list(arraySize(x)[0:2]) for x in index]
      print(index)
    
    # Check index
    if (not self.correctIndicies(index)):
      raise Exception('Incorrect array indexing')
    
    # Construct numpy array indexing
    arrayInd = []
    for dim, x in enumerate(index):
      arrayInd.append(np.array(range(x[0],x[1]+1)) - self.dimIndOffset[dim])
      print(arrayInd)
      # Flip indices if original declaration is
      if self.flipInd[dim]:
        arrayInd[-1] = self.array[dim][1] - self.dimIndOffset[dim] - arrayInd[-1]
        
      print(arrayInd)
      
    # Check if these values were already assigned
    alrdyAsgnd = np.any(self.initAsgnd[arrayInd])
    if (alrdyAsgnd):
      raise Exception('Variable Index assigned')
      
    # Assign value
    self.value[arrayInd] = node.value
    self.initAsgnd[arrayInd] = True
    
    if self.const:
      self.valAsgnd[arrayInd] = True
      
        
  def assignValue(self, node, index=None):
    # Verify type
    if (node.typeName != self.typeName):
      raise Exception('Variable Type Mismatch')
    
    if (index is None):
      index = deepcopy(self.array)
      index = [list(arraySize(x)[0:2]) for x in index]
    
    # Check index
    if (not self.correctIndicies(index)):
      raise Exception('Incorrect array indexing')
    
    # Construct numpy array indexing
    arrayInd = []
    for x in index:
      arrayInd.append(range(x[0],x[1]+1))
      
    # Check if these values were already assigned
    alrdyAsgnd = np.any(self.valAsgnd[arrayInd])
    if (alrdyAsgnd):
      raise Exception('Variable index already assigned')
      
    # Assign value
    self.valAsgnd[arrayInd] = True
    
    # Flip indices if they are defined reversed
    for dim,dimInd in enumerate(self.array):
      if (dimInd[0] > dimInd[1]):
        self.valAsgnd = flip(self.valAsgnd,dim)
    
  def correctIndicies(self,refInd):
    # See if declaration is array
    lenRef = len(refInd)-1
    for ind,varDim in enumerate(self.array):
      if (ind <= lenRef):
        # Dimension exists, check values of array
        refDim = arraySize(refInd[ind])
        if ((refDim[0] < varDim[0]) or (refDim[1] > varDim[1])):
          return False
        
      else:
        return False
        
    return True
    

class LibrarySymbol (BaseSymbol, SymbolTable):
  def __init__(self, node, encScope):
    BaseSymbol.__init__(self, node.name, 'library', node)
    SymbolTable.__init__(self, node.name, encScope.scopeLevel+1, encScope)
    self.nodes = []
    
class ModuleSymbol (BaseSymbol, SymbolTable):
  def __init__(self, node, scopeLevel, encScope):
    BaseSymbol.__init__(self, node.name, 'module', node)
    SymbolTable.__init__(self, node.name, scopeLevel, encScope)
    self.arch  = []
    self.gens  = []
    self.ports = []
    
class ArchSymbol (BaseSymbol, SymbolTable):
  def __init__(self, node, scopeLevel, encScope):
    BaseSymbol.__init__(self, node.name, 'arch', node)
    SymbolTable.__init__(self, node.name, scopeLevel, encScope)
