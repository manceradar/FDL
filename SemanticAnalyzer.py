from collections import OrderedDict
from copy import deepcopy
from NodeVisitor import NodeVisitor
from SymbolTable import SymbolTable
from Symbols import *
    
    
# Perform deeper analysis of AST
# Check if variables exist
# Check if types are defined
# Check indexing and slicing has constant variables
# Check array sizes match
class SemanticAnalyzer (NodeVisitor):
  def __init__(self,config):
    self.scope = SymbolTable('global',1,None)
    self.__builtin__(config)
    
  def __builtin__(self, config):
    # Loop over types
    for x in config['types']:
      typeSymbol = BuiltinTypeSymbol(x, self.scope.scopeLevel+1, self.scope)
      self.scope.insert(typeSymbol)
      
    self.scope.status()
    
  def compile(self, astList):
    # Visit all files
    for ast in astList:
      self.visit(ast)
      
    # Compile
    for ast in astList:
      self.compile(ast)
    
  def visit_file(self,node):
    # TODO: import
    for ind in node.importNodes:
      self.visit(ind)
    
    # Module
    self.visit(node.moduleNode)
    
    # Close file
    self.fid.close()
    
  def visit_module(self,node):
    # Check generic declarations
    for gen in node.genDeclNodes:
      self.visit(gen)
      
    # Check port declarations
    for port in node.portDeclNodes:
      self.visit(port)
      
    # Visit architecture
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
        raise Exception('{0} must be constant'.format(argSym.name))
       
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
    print(node.array)
    print(initVal)
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
          
