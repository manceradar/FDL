from copy import deepcopy
import numpy as np

from SymbolTable import SymbolTable
from SymbolCheckers import SignalChecker, ParamChecker, ReturnStmtChecker, IndexChecker, TypeTraitChecker


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
    # Symbol is a template type
    self._template   = False
    
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
    
  def isTemplate(self):
    return self._template
    
  def setTemplate(self):
    self._template = True
    
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

    
# Define generic symbols
class GenTypeSymbol (BaseSymbol, IndexChecker):
  def __init__(self, node):
    if (type(node.name).__name__ == 'str'):
      nodeName = node.name
    elif (type(node.name).__name__ == 'Token'):
      nodeName = node.name.value
    else:
      raise Exception('GenTypeSymbol Init Error')
      
    BaseSymbol.__init__(self, nodeName, 'generic', node)
    self.name        = nodeName
    self.typeDim     = None
    self.defaultType = node.defaultType
    self.typeBound   = node.typeBound
    self.setTemplate()

    
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
class BuiltinTypeSymbol (BaseSymbol, SymbolTable, ParamChecker, TypeTraitChecker):
  def __init__(self, configDict, encScope):
    # Define type from dict
    BaseSymbol.__init__(self,configDict['name'],'type')
    SymbolTable.__init__(self, configDict['name'], encScope.scopeLevel+1, encScope)
    TypeTraitChecker.__init__(self)
    
    # Param insertion
    for symDict in configDict['paramSym']:
      #node = ParamNode(configDict, ind)
      #self.insert(ParamSymbol(node))
      paramNode = ParamSymbol(symDict)
      self.insert(paramNode)
      
    self.verifyParamDecl()
    
  def addBuiltinMethod(self, builtinMethod):
    # Add builtin type signals
    for methodDef in builtinMethod:
      funcSym = TypeMethodSymbol(methodDef, self)
      self.insert(funcSym)
      
  def addTypeSymbol(self):
    # Add type symbols to parameters
    params = self.returnParams()
    for param in params:
      typeSym = self.lookup(param.typeName, 'type')
      param.addTypeSymbol(typeSym)
      
    # Add function param type symbols
    funcSymList = self.returnSymbolList(['function'])
    for funcSym in funcSymList:
      funcSym.addTypeSymbol()
      
    
# Define builtin function symbols from YAML config
class TypeMethodSymbol (BaseSymbol, SymbolTable, 
                        ParamChecker, ReturnStmtChecker):
  def __init__(self, configDict, encScope):
    BaseSymbol.__init__(self, configDict['name'], 'function')
    SymbolTable.__init__(self, configDict['name'], encScope.scopeLevel+1, encScope)
    ReturnStmtChecker.__initDict__(self, configDict)
    for symDict in configDict['returnSym']:
      returnSym = SignalSymbol(symDict, None, [])
      returnSym.setArray(symDict['array'])
      self.returnNodes.append(returnSym)
    
    # Insert param symbols
    for symDict in configDict['paramSym']:
      paramNode = ParamSymbol(symDict)
      self.insert(paramNode)
    
    # Verify params
    self.verifyParamDecl()
    self.funcDef = False
    
  def addTypeSymbol(self):
    # Add type symbols to parameters
    params = self.returnParams()
    for param in params:
      typeSym = self.lookup(param.typeName, 'type')
      param.addTypeSymbol(typeSym)
    
# Define builtin process from YAML config
class ProcessSymbol (BaseSymbol, SymbolTable, ParamChecker):
  def __init__(self, configDict, encScope):
    # Define type from dict
    BaseSymbol.__init__(self,configDict['name'],'process')
    SymbolTable.__init__(self, configDict['name'], encScope.scopeLevel+1, encScope)
    
    # Param insertion
    for ind in range(len(configDict['paramTypeName'])):
      node = ParamNode(configDict, ind)
      self.insert(ParamSymbol(node))
      
    self.verifyParamDecl()
    
class LibrarySymbol (BaseSymbol, SymbolTable):
  def __init__(self, node, encScope):
    if (type(node).__name__ == 'BaseAST'):
      self.__initGen__(node.name, encScope, node)
    elif (type(node).__name__ == 'Token'):
      self.__initGen__(node.value, encScope, None)
    else:
      raise Exception('LibrarySymbol Init Error')
  def __initGen__(self, nodeName, encScope, node):
    BaseSymbol.__init__(self, nodeName, 'library', node)
    SymbolTable.__init__(self, nodeName, encScope.scopeLevel+1, encScope)
    self.nodes = []
    
class AttributeSymbol (BaseSymbol):
  def __init__(self, node, type):
    BaseSymbol.__init__(self, node.name, 'attr', node)
    self.name  = node.name
    self.value = node.value
    self.attrType  = type
    
class AssertSymbol (BaseSymbol):
  def __init__(self, node):
    BaseSymbol.__init__(self, 'TBD_ASSERT', 'assert', node)
    
class ModuleSymbol (BaseSymbol, SymbolTable):
  def __init__(self, node, encScope):
    BaseSymbol.__init__(self, node.name, 'module', node)
    SymbolTable.__init__(self, node.name, encScope.scopeLevel+1, encScope)
    self.arch  = []
    self.gens  = []
    self.ports = []
    
class ArchSymbol (BaseSymbol, SymbolTable):
  def __init__(self, node, encScope):
    BaseSymbol.__init__(self, node.name, 'arch', node)
    SymbolTable.__init__(self, node.name, encScope.scopeLevel+1, encScope)
        
# Define structure symbol for data consolidation
class StructSymbol (BaseSymbol, SymbolTable, ParamChecker, Field, TypeTraitChecker):
  def __init__(self, node, encScope):
    BaseSymbol.__init__(self, node.name, 'type', node)
    SymbolTable.__init__(self, node.name, encScope.scopeLevel+1, encScope)
    Field.__init__(self)
    TypeTraitChecker.__init__(self)
    
# Define interface symbol for data consolidation
class InterfaceSymbol (BaseSymbol, SymbolTable, ParamChecker, Field, TypeTraitChecker):
  def __init__(self, node, encScope):
    BaseSymbol.__init__(self, node.name, 'type', node)
    SymbolTable.__init__(self, node.name, encScope.scopeLevel+1, encScope)
    Field.__init__(self)
    TypeTraitChecker.__init__(self)
    
# Define trait symbol for class interface definitions
class TraitSymbol (BaseSymbol, SymbolTable, ParamChecker):
  def __init__(self, node, encScope):
    BaseSymbol.__init__(self, node.name.value, 'trait', node)
    SymbolTable.__init__(self, node.name.value, encScope.scopeLevel+1, encScope)
    self.setTrait(True)

# Define implement symbol for class interface implementation
class ImplSymbol (BaseSymbol, SymbolTable):
  def __init__(self, node, encScope):
    BaseSymbol.__init__(self, node.name, 'impl', node)
    SymbolTable.__init__(self, node.name, encScope.scopeLevel+1, encScope)

# Define user defined function symbol
class FuncSymbol (BaseSymbol, SymbolTable, ParamChecker, ReturnStmtChecker):
  def __init__(self, node, encScope):
    print('\n'.join(node.log()))
    BaseSymbol.__init__(self, node.name.value, 'function', node)
    SymbolTable.__init__(self, node.name.value, encScope.scopeLevel+1, encScope)
    ReturnStmtChecker.__initClass__(self)
    self.funcDef        = node.funcDef
    
class EnumSymbol (BaseSymbol):
  def __init__(self,name,states):
    BaseSymbol.__init__(name, 'type')
    self.states = states
    
class EnumStateSymbol (BaseSymbol):
  def __init__(self, name):
    BaseSymbol.__init__(name, 'state')
  

# Define symbols from builtin or user defined sources
class ParamSymbol (BaseSymbol, SignalChecker, IndexChecker):
  def __init__(self, node):
    if (type(node).__name__ == 'BaseAST'):
      self.__initClass__(node)
    elif (type(node).__name__ == 'dict'):
      self.__initDict__(node)
      
    self.typeSym     = None
    self.value       = None
    self.const       = False
    self.setParameter()
      
  def __initClass__(self, node):
    BaseSymbol.__init__(self, node.name, 'signal', node)
    self.typeName    = node.type
    self.typeDim     = node.dim
    
    
  def __initDict__(self, node):
    BaseSymbol.__init__(self, node['name'], 'signal')
    self.typeName    = node['typeName']
    self.typeDim     = self.determineDim(node['array'])
    
  def addTypeSymbol(self, typeSym):
    self.typeSym     = typeSym

# 
class SignalSymbol (BaseSymbol, SignalChecker, IndexChecker):
  def __init__(self, node, typeSym, inputParams):
    if (type(node).__name__ == 'BaseAST'):
      self.__initClass__(node)
    elif (type(node).__name__ == 'dict'):
      self.__initDict__(node)
      
    self.typeParams  = inputParams
    self.typeSym     = typeSym
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
    if (type(node.name).__name__ == 'str'):
      nodeName = node.name
    elif (type(node.name).__name__ == 'Token'):
      nodeName = node.name.value
    else:
      raise Exception('SignalSymbol Init Error')
      
    BaseSymbol.__init__(self, nodeName, 'signal', node)
    self.typeName    = node.typeName.name
    if (node.base is 'CONST'):
      self.typeDim   = 0
    else:
      self.typeDim   = self.determineDim(node.array)
    self.const       = node.const
    self.portType    = node.port
    
  def __initDict__(self, node):
    BaseSymbol.__init__(self, node['name'], 'signal')
    self.typeName    = node['typeName']
    self.typeDim     = self.determineDim(node['array'])
    self.const       = node['const']
    self.portType    = node['port']
    
  #def addTypeSymbol(self, typeSym):
  #  self.typeSym     = typeSym
  
  def setGeneric(self):
    self.generic = True
    
  def isGeneric(self):
    return self.generic
    
  def setPort(self):
    self.port = True
    
  def isPort(self):
    return self.port
    
  def setArray(self, array):
    self.flipInd     = [x[0] > x[1] for x in array]
    self.array       = [list(self.arraySize(x)[0:2]) for x in array]
    
    arrayDim = tuple([self.arraySize(ind)[2] for ind in array])
    
    self.dimIndOffset  = [self.arraySize(ind)[0] for ind in array]
    
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
      index = [list(self.arraySize(x)[0:2]) for x in index]
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
      index = [list(self.arraySize(x)[0:2]) for x in index]
    
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
        self.valAsgnd = self.flip(self.valAsgnd,dim)
    
  def correctIndicies(self,refInd):
    # See if declaration is array
    lenRef = len(refInd)-1
    for ind,varDim in enumerate(self.array):
      if (ind <= lenRef):
        # Dimension exists, check values of array
        refDim = self.arraySize(refInd[ind])
        if ((refDim[0] < varDim[0]) or (refDim[1] > varDim[1])):
          return False
        
      else:
        return False
        
    return True
    

