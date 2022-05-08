from collections import OrderedDict
from copy import deepcopy
from .NodeVisitor import NodeVisitor
from .SymbolTable import SymbolTable
from .Symbols import *
    
    
# Perform deeper analysis of AST
# Check if variables exist
# Check if types are defined
# Check indexing and slicing has constant variables
# Check array sizes match
class SemanticAnalyzer (NodeVisitor):
  def __init__(self, config, builtin_libs):
    self.scope = SymbolTable('global',1,None)
    self.__builtin__(config)
    
    # Visit all builtin libraries
    #for lib in builtin_libs:
    #  # Add all nodes
    #  for node in lib.nodes[0].nodes:
    #    self.visit(node)
    
  def __builtin__(self, config):
    # Loop over types
    for x in config['types']:
      typeSymbol = BuiltinTypeSymbol(x, self.scope.scopeLevel+1, self.scope)
      self.scope.insert(typeSymbol)
      
    # Loop over functions
    for x in config['func']:
      funcSymbol = FuncSymbol(x, self.scope.scopeLevel+1, self.scope)
      self.scope.insert(funcSymbol)
      
    # Loop over attributes
    for x in config['attr']:
      attrSymbol = AttrSymbol(x, self.scope.scopeLevel+1, self.scope)
      self.scope.insert(attrSymbol)
      
    self.scope.status()
    
  def process(self, astList):
    # Visit all files
    for ast in astList:
      self.visit(ast)
      
    # Compile
    for ast in astList:
      self.compile(ast)
    
  def visit_file(self, node):
    # Go to nodes
    for ind in node.nodes:
      self.visit(ind)
      
  def visit_library(self, node):
    # Create new library scope
    libSym = LibrarySymbol(node, self.scope)
    
    # Set library as new scope
    self.scope = libSym
    
    # Loop over nodes
    for node in node.nodes:
      self.visit(node)
      self.scope.status()
    
  def visit_module(self,node):
    # Check generic declarations
    for gen in node.genDeclNodes:
      self.visit(gen)
      
    # Check port declarations
    for port in node.portDeclNodes:
      self.visit(port)
    
  def visit_archblock(self, node):
    # Loop over signal declarations
    for sig in node.sigDeclNodes:
      self.visit(sig)
      
    self.scope.status()
      
    # Loop through statements
    for sm in node.statements:
      self.visit(sm)
      
  def visit_function(self, node):
    # Create symbol and set new scope
    func = FuncSymbol(node, self.scope.scopeLevel+1,self.scope)
    self.scope = func
    
    # Check input parameters
    for param in node.params:
      # Verify data type
      self.scope.lookup(param.type, 'type')
      
      # Create param symbol and insert into function scope
      paramSym = ParamSymbol(param)
      self.scope.insert(paramSym)
      
    # Verify param declarations for this function
    func.verifyParamDecl()
    
    # Loop over statements in
    for stmt in node.statements:
      self.visit(stmt)
      
    # Return back original scope
    self.scope = self.scope.enclosingScope
      
    # Statements validated, now add overloaded functions
    params = func.returnParams()
    
    names = calcAllFuncNames(func.name, params)
    for name in names:
      func.name = name
      self.scope.insert(func)
      
    self.scope.status()
      
  def visit_return(self, node):
    # Look up types and dimensions
    for var in node.vars:
      varSym = self.visit(var)
      self.scope.returnTypeName.append(varSym.typeName)
      self.scope.returnTypeDim.append(varSym.typeDim)
    
      
  def visit_decl(self, node):
    # Check declarations
    
    # Verify type exists
    typeDef = self.scope.lookup(node.typeName, 'type')
    
    # Verify input parameters 
    paramSym = [self.visit(param) for param in node.params]
    params = typeDef.verifyInputs(paramSym)
       
    # Replace array indicies with values
    self.checkArray(node)
    
    # Type, array size, and init value verified
    varDecl = SignalSymbol(node, params)
    varDecl.setArray(node.array)
    
    # Validate Init value
    if (node.value != None):
      # No interface port can have value
      if (node.port is None):
        # Visit node
        initVar = self.visit(node.value)
        
        varDecl.assignInitValue(initVar)
      else:
        print('Ports can not have init value')
        raise Exception('Port Init')
    
    varAdded  = self.scope.insert(varDecl)
    
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
      
  def visit_assignment(self, node):
    leftVar = self.visit(node.leftVar)
    
    rightExpr = self.visit(node.rightExpr)
    
  def visit_array(self, node):
    # load elements
    elements = []
    dtypes = []
    for elem in node.nodes:
      elemSym = self.visit(elem)
      elements.append(elemSym)
      dtypes.append(elemSym.type)
      
    return (elements, dtypes)
      
  def visit_expr(self, node):
    # First visit node to verify it
    # Validate 'left'
    left = self.visit(node.left)
    op = node.op
    right = self.visit(node.right)
    
    if (left.const):
      lStr = str(left.value[0])
    else:
      lStr = left.name
      
    if (right.const):
      rStr = str(right.value[0])
    else:
      rStr = right.name
      
    if (op == '&'):
      array = [arraySize(left.array[0])[2]+right.array[0][0], right.array[0][1]]
    else:
      array = left.array
      
    resultStr = lStr + op + rStr
    if (left.const and right.const):
      resultStr = eval(resultStr)
    
    result = deepcopy(left)
    result.value = [resultStr]
    result.array = array
    return result
    
  def visit_term(self,node):
    # First visit node to verify it
    # Validate 'left'
    leftValid = self.visit(node.left)
    op = node.op
    rightValid = self.visit(node.right)
    
    return leftValid
      
  def visit_factor(self,node):
    # Validate
    return self.visit(node)
    
  def visit_const(self, node):
    # Number, return values
    sigSym = SignalSymbol(node, node.params)
    sigSym.setArray([[0,0]])
    sigSym.assignConstValue(node.value)
    return sigSym
    
  def visit_var(self, node):
    # Replace array indicies with values
    self.checkArray(node)
    
    declNode = self.scope.lookup(node.name, 'signal')
    declNode.gotReferenced()
    
    return declNode
      
  def checkArray(self, node):
    if (node.array == None):
      return
      
    # If var is a declaration, array values must be const
    isDecl = node.decl
    
    # Check array sizes use constants
    arrayVal = node.array
    for i,arg in enumerate(node.array):
      for j,val in enumerate(arg):
        
        # Visit expr
        varSym = self.visit(val)
        
        # Variables must be integer
        typeValid = varSym.typeName in ['sint','uint']
        
        # Truth table to error when isDecl and varSym is not const
        constValid = not(isDecl) or varSym.const
        
        if (constValid and typeValid):
          # If value is none, just give name
          #print(varSym)
          if (varSym.value is None):
            arrayVal[i][j] = varSym.name
          else:
            arrayVal[i][j] = varSym.value[0]
          
        else:
          raise Exception('ArrayInd bad')
          
