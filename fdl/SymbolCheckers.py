from copy import deepcopy

class TypeTraitChecker(object):
  def __init__(self):
    self.traitSymList = []
  
  def addTraitSym(self, traitSym):
    self.traitSymList.append(traitSym)

class SignalChecker(object):
  def flip(self,m,axis):
    if not hasattr(m, 'ndim'):
      m = asarray(m)
    indexer = [slice(None)] * m.ndim
    try:
      indexer[axis] = slice(None, None, -1)
    except IndexError:
      raise ValueError("axis=%i is invalid for the %i-dimensional input array"
                         % (axis, m.ndim))
    return m[tuple(indexer)]
  
  def determineDim(self,array):
    # Determine dimensions of input parameter
    numDim = 0
    for dim in array:
      # loop over dimensions
      if (dim[0] != dim[1]):
        numDim += 1
        
    return numDim
  
  def arraySize(self,array):
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
    
    
class IndexChecker(object):
  # Used for simple indexing, before validating array is defined
  def verifySimpleIndex(self, index):
    # Determine type dimensions with given index. This is a quick check,
    # not validating if indices are out of range. We will do that on 
    # second path.
    numDim = self.typeDim
    
    if index is None:
      return
      
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
    
# All symbols that have parameter inputs use this class to verify 
# inputs and declarations
class ParamChecker (object):
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
    
  def verifyInputs(self, inputNodes):
    # Check number of params
    lenArgs = len(inputNodes)
    
    if (lenArgs > self.numArgs):
      #Too many params
      raise('"{0}" has {1} params but {2} given.'.format(self.name, self.numArgs, lenArgs))
    
    # Loop over input params
    params = self.returnParams()
    
    inputValues = []
    for ind,node in enumerate(inputNodes):
      # Check params match
      if (node.typeName not in params[ind].typeName):
        raise Exception('{0}: {1} type does not match {2}.'.format(params[ind].name, node.typeName, params[ind].typeName))
        
      # Check dimensions
      if (node.typeDim != params[ind].typeDim):
        raise Exception('{0} dims does not match {1}.'.format(node.name, params[ind].name))
        
      # Check if value is defined
      if (node.value is not None):
        # Param defined, takes priority over default value
        value = deepcopy(node.value)
      elif (params[ind].value is not None):
        value = deepcopy(params[ind].value)
      else:
        raise Exception('{0} does not have default value.'.format(params[ind].name))
        
      # Append input
      inputValues.append((params[ind].name, value))
      
    # Loop over parameters not defined, if they exist
    for ind in range(lenArgs,self.numArgs):
      inputValues.append((params[ind].name, deepcopy(params[ind].value)))
          
    return inputValues
    
    
class ReturnStmtChecker(object):
  def __initClass__(self):
    self.returnTypeName = []
    self.returnTypeDim  = []
    self.numReturnArgs  = 0
    self.returnNodes    = []
    
  def __initDict__(self, configDict):
    self.returnTypeName = configDict['returnTypeName']
    self.returnTypeDim  = configDict['returnTypeDim']
    self.numReturnArgs  = len(self.returnTypeName)
    self.returnNodes    = []
    
  def verifyReturnStmt(self, returnNodes):
    # Check number of params
    lenArgs = len(returnNodes)
    
    if (lenArgs != self.numReturnArgs):
      #Too many params
      raise Exception('"{0}" has {1} return arguments but {2} given.'.format(self.name, self.numReturnArgs, lenArgs))
    
    for ind,node in enumerate(returnNodes):
      # Check params match
      if (node.typeName[-1] not in self.returnTypeName[ind]):
        raise Exception('{0}: {1} type does not match {2}.'.format(node.name, node.typeName, self.returnTypeName[ind]))
        
      # Check dimensions
      if (node.typeDim != self.returnTypeDim[ind]):
        raise Exception('{0}: Dimension does not match {1} =/= {2}.'.format(node.name, node.typeDim, self.returnTypeDim[ind]))
        
      # Append input
      self.returnNodes.append((returnNodes[ind].name, deepcopy(node.value)))
