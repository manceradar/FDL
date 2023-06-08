from collections import OrderedDict
from copy import deepcopy,copy
from NodeVisitor import NodeVisitor
from SymbolTable import SymbolTable
from Symbols import *
#from Symbol

import os.path

    
# Perform deeper analysis of AST
# Check if variables exist
# Check if types are defined
# Check indexing and slicing has constant variables
# Check array sizes match
class SemanticAnalyzer (NodeVisitor):
  def __init__(self, config, lib_path):
    # Create Symbol table
    self.scope = SymbolTable('global', 0, None)
    
    # Load base types and attributes
    self.__builtin__(config)
    
    # Base paths
    self.path = []
    self.path.extend(lib_path)
    
    # Collection of all ASTs
    self.astList = []
    
  def __builtin__(self, config):
    # Loop over type functions
    self.builtinMethod = config['builtinMethod']
      
    # Loop over types
    for x in config['types']:
      typeSymbol = BuiltinTypeSymbol(x, self.scope)
      typeSymbol.addBuiltinMethod(self.builtinMethod)
      added = self.scope.insert(typeSymbol)
      if not(added):
        raise Exception('Cannot add symbol {0}.'.format(typeSymbol.name))
        
    # Now get all type symbols and add type symbols to param nodes
    typeSymList = self.scope.returnSymbolList(['type'])
    for typeSym in typeSymList:
      typeSym.addTypeSymbol()
      
    self.scope.status()
    
  def addPath(self, addedPath):
    # Add more paths to search
    self.path.extend(addedPath)
    
  def nextScope(self, newScope, replaceEnclosingScope=False):
    # If replacingEnclosingScope is true, this means the newScope's 
    # needs to be replaced temporarily to allow correct scoping during
    # symbol searches. for example, type implementations need this
    # feature on. The base type's enclose scope is global but during
    # implementation, the enclosing scope needs to be the implementation.
    self.replaceEnclosingScope = replaceEnclosingScope
    
    if (replaceEnclosingScope):
      self.oldEnclosingScope = newScope.enclosingScope
      newScope.enclosingScope = self.scope
    
    # Move to new symbol table scope
    self.scope = newScope
    
  def previousScope(self):
    # go back to previous scope
    
    
    if (self.replaceEnclosingScope):
      desiredScope = self.scope.enclosingScope
      self.scope.enclosingScope = self.oldEnclosingScope
      self.scope = desiredScope
    else:
      self.scope = self.scope.enclosingScope
      
    
  def pre_process(self, ast):
    # First we need to add AST to the AST list
    self.astList.append(ast)
    
    # Next, search file for all import statements
    importPaths = []
    for node in ast.nodes:
      # Verify if node is import
      if (node.base.lower() == 'import'):
        filename = self.pre_process_import(node)
        importPaths.append(filename)
          
    return importPaths
    
  def pre_process_import(self, node):
    # Verify path name
    importName = os.path.join(*[load.value for load in node.load])
    importName += '.fdl'
    
    # Loop through all paths, and check for duplicates
    fileExists = False
    filePath = ''
    for path in self.path:
      # New path
      fullImportPath = os.path.join(path, importName)
      
      exists = os.path.exists(fullImportPath)
      if exists:
        # If fileExists is already true, then we have a duplicate
        if fileExists:
          raise Exception('File path duplicates, "{0}" and "{1}"'.format(filePath, path))
        
        fileExists = True
        filePath = fullImportPath
        
    # If file not found, throw error
    if not(fileExists):
      raise Exception('Import path not found, {0}'.format(importName))
    
    return (filePath, node.load)
    
  def process(self):
    # Visit all ASTs
    for ast in self.astList:
      self.visit(ast)
    
  def visit_file(self, node):
    # Create library symbol to encompass file
    fileSym = LibrarySymbol(node, self.scope)
    added = self.scope.insert(fileSym)
    if not(added):
      raise Exception('Cannot add file {0}, already exists.'.format(node.name))
    
    # Set library as new scope
    self.nextScope(fileSym)
    
    # Go to nodes
    for ind in node.nodes:
      self.visit(ind)
      
    # Go back to original scope
    self.previousScope()
    print('File status')
    self.scope.status()
      
  def visit_import(self, node):
    # Keep current scope
    currentScope = self.scope
    
    # First, see if the library has been processed
    for lib in node.load[0:-1]:
      libSym = self.scope.lookup(lib.value, 'library', printError=False)
      
      # If libSym is None, symbol not found so create it
      if libSym == None:
        # Create library symbol to encompass file
        fileSym = LibrarySymbol(lib, self.scope)
        added = self.scope.insert(fileSym)
        if not(added):
          raise Exception('Cannot add symbol {0}.'.format(fileSym.name))
        
        # Set library as new scope
        self.nextScope(fileSym)
      else:
        # Symbol found, move to new scope
        self.nextScope(libSym)
  
    # Verify if library is processed, if not then create it from AST
    libSym = self.scope.lookup(node.load[-1].value, 'library', printError=False)
    if libSym == None:
      print('{0} library not found, processing...'.format(node.name))
      # Find AST with import name and process
      for ast in self.astList:
        if (ast.importName == node.load):
          
          # Process library
          self.visit(ast)
          break
    
    # Get processed scope
    libSym = self.scope.lookup(node.load[-1].value, 'library')
    
    # Link to existing scope
    self.scope = currentScope
    added = self.scope.insert(libSym, False)
    if not(added):
      raise Exception('Cannot add symbol {0}.'.format(libSym.name))
    print('Import status')
    self.scope.status()
      
  def visit_library(self, node):
    # Create new library scope
    libSym = LibrarySymbol(node, self.scope)
    
    # Set library as new scope
    self.nextScope(libSym)
    
    # Loop over nodes
    for node in node.nodes:
      self.visit(node)
      
    self.previousScope()
    added = self.scope.insert(libSym)
    if not(added):
      raise Exception('Cannot add symbol {0}.'.format(libSym.name))
      
  def visit_trait(self, node):
    traitSym = TraitSymbol(node, self.scope)
    
    # Check input generics
    for gen in node.generics:
      # Create GenType symbol and insert into trait scope
      genSym = GenTypeSymbol(gen)
      
      traitSym.insert(genSym)
      
    # Move scope
    self.nextScope(traitSym)
    
    # Load all trait statements
    for stmt in node.nodes:
      self.visit(stmt)
      
    # Go back scope
    self.previousScope()
    self.scope.insert(traitSym)
    
  def visit_impl(self,node):
    # First, verify type name exists
    typeSym = self.lookupName(node.name)
    if typeSym is None:
      # Type not found, error
      raise Exception('Impl: Type "{0}" not found'.format(typeSym.name))
      
    # Set type as scope
    self.nextScope(typeSym,replaceEnclosingScope=True)
    
    # Set implementation true in scope
    self.scope.setImpl(True)
    
    # Check generic types
    genSymList = []
    for gen in node.typeGeneric:
      # Check type exists
      genSym = self.lookupName(gen.name)
      
      # Verify that default and typeBounds is not set
      if (not genSym.typeBound.empty()):
        raise Exception('Impl: Type Generic "{0}" should not have type bound in implementation'.format(genSym.name))
    
      if (genSym.defaultValue is not None):
        raise Exception('Impl: Type Generic "{0}" should not have default value in implementation'.format(genSym.name))
      
      genSymList.append(genSym)
      
    # Implementation for types
    if node.traitImpl is False:
      self.impl_type(node, genSymList)
    else:
      self.impl_trait(node, genSymList)
      
    # Set implementation False, implementation done
    self.scope.setImpl(False)
    
    # Done, return back to original scope
    self.previousScope()
    
  def impl_type(self, node, genSymList):
    # Basic implementation
    if (not node.nodes):
      # Type not found, error
      raise Exception('Impl: Type "{0}" requires definitions'.format(self.name))
      
    # Loop over all nodes.
    for stmt in node.nodes:
      self.visit(stmt)
      
    #self.scope.status()
    #self.scope.statu()
    
  def impl_trait(self, node, genSymList):
    # Load trait
    traitSym = self.lookupName(node.traitName)
    self.scope.addTraitSym(traitSym)
    
    # Trait implementation
    if (not node.nodes):
      # Type not found, error
      raise Exception('Impl: Type "{0}" requires definitions'.format(self.name))
      
    # Loop over all nodes.
    for stmt in node.nodes:
      self.visit(stmt)
      
    #self.scope.status()
    
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
    funcSym = FuncSymbol(node, self.scope)
    
    # Check input parameters
    for param in node.params:
      # If param type is Self in impl, set to actual data type
      typeName = param.type.name[-1].value
      
      # Check if we need to replace Self with datatype used in impl
      if (self.scope.impl and (typeName == 'Self')):
        typeSym = self.scope
      else:
        # Normal check, verify data type
        typeSym = self.lookupName(param.type)
      
      # Replace type name
      param.type = typeSym.name
      
      # Create param symbol
      paramSym = ParamSymbol(param)
      paramSym.addTypeSymbol(typeSym)
      
      # insert into function scope
      funcSym.insert(paramSym)
      
    # Verify param declarations for this function
    funcSym.verifyParamDecl()
    
    # Check return parameters
    for returnNode in node.returnType:
      # If param type is Self in impl, set to actual data type
      typeName = returnNode.type.name[-1].value
      
      # Check if we need to replace Self with datatype used in impl
      if (self.scope.impl and (typeName == 'Self')):
        sym = self.scope
      else:
        # Normal check, verify data type
        sym = self.lookupName(returnNode.type)
      
      # Replace type name
      funcSym.returnTypeName.append(sym.name)
      funcSym.returnTypeDim.append(returnNode.dim)
      funcSym.numReturnArgs += 1
      
      
    # Statements validated
      
    # If only function definition, then return
    if (funcSym.trait or funcSym.funcDef):
      # Create overloaded symbols
      self.createOverloadedSymbols(funcSym)
      return
      
    # Move scope and add statements
    self.nextScope(funcSym)
    
    # Load declarations if necessary
    if node.declareBlock is not None:
      for decl in node.declareBlock.declNodes:
        print('Declare Node')
        self.visit(decl)
      
    # Loop over statements in
    for stmt in node.logicBlock.statements:
      self.visit(stmt)
      
    # Return to old scope
    self.previousScope()
    
    # Create overloaded symbols
    self.createOverloadedSymbols(funcSym)
    #print('func scope')
    #self.scope.status()
      
  def visit_return(self, node):
    # Look up types and dimensions
    returnSym = []
    for var in node.vars:
      sym = self.visit(var)
      sym.gotReferenced()
      returnSym.append(sym)
      
    # Verify return statements
    self.scope.verifyReturnStmt(returnSym)
      
  def visit_attr(self, node):
    # Determine if the attribute is added to itself or next reference
    
    for spec in node.spec:
      # Create attribute spec
      attrSym = AttributeSymbol(spec, node.type)
      
      # Insert symbol, no lookup required
      self.scope.insert(attrSym)
      
  def visit_assert(self, node):
    # We will check condition and report message later
    assertSym = AssertSymbol(node)
    
    self.scope.insert(assertSym)
      
  def visit_decl(self, node):
    # Check declarations
    
    # Verify type exists
    typeSym = self.lookupName(node.typeName)
    
    # Verify input parameters
    paramSymList = []
    for param in node.params:
      paramSym = self.visit(param)
      
      if type(paramSym) is list:
        # functions could return multiple values, which is not allowed
        if (len(paramSym) != 1):
          raise Exception('Parameter function returned multiple values, not allowed')
        
        paramSym = paramSym[0]
      
      paramSymList.append(paramSym)
      
    params = typeSym.verifyInputs(paramSymList)
       
    # Replace array indicies with values
    self.checkArray(node)
    
    # Type, array size, and init value verified
    varDecl = SignalSymbol(node, typeSym, params)
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
    left = self.visit(node.params[0])
    op = node.op
    right = self.visit(node.params[1])
    
    # If symbols are list, funccall was used and we need to verify its only 1 return
    if (isinstance(left,list)):
      if (len(left) > 1):
        raise Exception('Cannot use func call that returns more than one value in expression')
      left = left[0]
      
    if (isinstance(right,list)):
      if (len(right) > 1):
        raise Exception('Cannot use func call that returns more than one value in expression')
      right = right[0]
    
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
    # Verify type exists
    typeSym = self.lookupName(node.typeName)
    
    # Number, return values
    sigSym = SignalSymbol(node, typeSym, node.params)
    sigSym.setArray([[0,0]])
    sigSym.assignConstValue(node.value)
    return sigSym
    
  def visit_var(self, node):
    # Replace array indicies with values
    #self.checkArray(node)
    
    declNode = self.scope.lookup(node.name, 'signal')
    declNode.gotReferenced()
    
    typeSym = declNode.typeSym
    if typeSym is None:
      self.scope.statu()
    
    oldScope = self.scope
    
    self.nextScope(typeSym)
    
    # Check if variable has field
    if (node.field is not None):
      declNode = self.visit(node.field)
    
    # Check if method was used
    if (node.method is not None):
      declNode = self.visit(node.method)
      
    self.nextScope(oldScope)
    
    return declNode
    
  def visit_funccall(self, node):
    # Load function symbol
    if node.method:
      funcSym = self.scope.lookup(node.name, 'function', recursive=False)
    else: 
      funcSym = self.scope.lookup(node.name, 'function')
      
    # TODO check generics
    
    # Check parameters
    funcSym.verifyInputs(node.params)
    
    return funcSym.returnNodes
    
      
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
        typeValid = varSym.typeName[-1] in ['sint','uint']
        
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
          
  def lookupName(self, node):
    # This scope
    oldScope = self.scope
    
    # See if library needs to be loaded
    libName = node.name[0:-1]
    for lib in libName:
      # Lookup library and change scope
      libSym = self.scope.lookup(lib, 'library')
      if libSym == None:
        raise Exception('Name lookup failed')
        
      self.nextScope(libSym)
      
    # Lookup name
    if (node.base == 'TYPE'):
      symType = ['type', 'generic']
    else:
      symType = node.base.lower()
    
    sym = self.scope.lookup(node.name[-1], symType)
    if sym == None:
      raise Exception('Name lookup failed')
      
    # Goback to original scope
    self.scope = oldScope
      
    return sym
    
  def createOverloadedSymbols(self, funcSym):
    # Get input parameters, and create overloaded function names
    params = funcSym.returnParams()
    names = self.calcAllFuncNames(funcSym.name, params)
    
    # Add names to scope
    for name in names:
      funcSymCopy = copy(funcSym)
      funcSymCopy.name = name
      self.scope.insert(funcSymCopy)
    
  def calcAllFuncNames(self,funcName, inputs):
    # Determine all function names for function
    
    # Calculate name with no inputs
    defaultInd = np.array([x.value == None for x in inputs])
    if (len(inputs) == 0):
      defaultParam = inputs
    else:
      defaultParam = list(np.array(inputs)[defaultInd])
      
    names = [self.calcOverloadFuncName(funcName, defaultParam)]
    print(names)
    
    for ind in range(0,len(inputs)):
      if (inputs[ind].value != None):
        name = self.calcOverloadFuncName(funcName, inputs[0:ind+1])
        names.append(name)
        print(names)
      
    return names
    
  def calcOverloadFuncName(self,funcName, inputs):
    # Determine function name with one that can be resolved
    for x in inputs:
      funcName += '_{0}{1}'.format(x.typeName, x.typeDim)
      
    return funcName
