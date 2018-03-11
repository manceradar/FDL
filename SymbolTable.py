from collections import OrderedDict

class SymbolTable (object):
  def __init__(self,scopeName,scopeLevel,enclosingScope):
    # Initialize symbol table, it is list inside a dict.
    # The outer dict checks for symbol name, and inner list
    # has what that symbol means. 
    self._symbol        = OrderedDict()
    self.scopeName      = scopeName
    self.scopeLevel     = scopeLevel
    self.enclosingScope = enclosingScope
       
  def insert(self, symbol):
    # Inserts symbol into table, and checks for replicas
    # Returns bool if it was inserted
    
    # Look up symbol name
    lookupSym = self.lookup(symbol.name, symbol.type, False)
    
    # Add symbol
    if (lookupSym is None):
      self._symbol[symbol.name] = (symbol.type, symbol)
      return True
    else:
      return False
    
  def lookup(self, name, type, printError=True):
    # Look for type in current scope
    symbolList = self._symbol.get(name)
    
    if (symbolList is None):
      # Symbol not found, look in enclosing scope
      if (self.enclosingScope is None):
        # All scopes didnt find type
        if (printError):
          print('Symbol Name "{0}", Type "{1}" not found'.format(name, type))
        return None
      else:
        return self.enclosingScope.lookup(name, type, printError)
        
    else:
      # Symbol found, check if type exists
      if (type == 'all'):
        return symbolList[1]
      elif (type == symbolList[0]):
        # Return symbol for index
        return symbolList[1]
        
  def returnParams(self):
    params = []
    for name,sym in self._symbol.iteritems():
      if (sym[1].isParameter()):
        params.append(sym[1])
          
    return params
    
  def removeImports(self):
    # Look for all imports and remove them
    for name,sym in self._symbol.iteritems():
      if (sym[1].isImported()):
        del self._symbol[name]
        
  def status(self):
    # Plot header
    width = 100
    header = '|{0}|'.format('Scope Symbol Table'.center(width-2,' '))
    scopeDetail = '|{0}|'.format('Name: "{0}", Scope: {1}'.format(self.scopeName, self.scopeLevel).center(width-2,' '))
    lines = ['=' * width, header, scopeDetail, '=' * width]
    
    linesType = self.statusTypes(width)
    if (linesType[0]):
      lines += linesType[1]
      
    linesFunc = self.statusFunctions(width)
    if (linesFunc[0]):
      lines += linesFunc[1]
      
    linesAttr = self.statusAttributes(width)
    if (linesAttr[0]):
      lines += linesAttr[1]
      
    linesLib = self.statusLibrary(width)
    if (linesLib[0]):
      lines += linesLib[1]
      
    linesMod = self.statusModules(width)
    if (linesMod[0]):
      lines += linesMod[1]
      
    linesVars = self.statusVariables(width)
    if (linesVars[0]):
      lines += linesVars[1]
    
    lines.append('='*width)
    lines.append('')
    print('\n'.join(lines))
    
  def statusTypes(self, width):
    # Initialize output
    lines = []
    
    # Plot types
    typeWidth = (width-2)/4
    leftOver = ' '*(width - 2 - 4*typeWidth)
    
    # Create header
    nameStr = 'Name'.ljust(typeWidth,' ')
    paramNameStr = 'Param Name'.ljust(typeWidth,' ')
    paramTypeStr = 'Type[Dim]'.ljust(typeWidth,' ')
    paramInitStr = 'Init. Value'.ljust(typeWidth,' ')
    lines.append('|{0}|'.format('Types'.center(width-2,' ')))
    lines.append('-'*width)
    lines.append('|{0}{1}{2}{3}{4}|'.format(nameStr, paramNameStr, paramTypeStr, paramInitStr, leftOver))
    lines.append('-'*width)
    
    # List types
    found = False
    for name,sym in self._symbol.iteritems():
      if sym[0] is 'type':
        found = True
        symbol = sym[1]
        params = symbol.returnParams()
        paramName = [param.name for param in params]
        paramTypeDim = ['{0}[{1}]'.format(param.typeName, param.typeDim) for param in params]
        tmp0 = symbol.name.ljust(typeWidth,' ')
        tmp1 = ','.join(paramName).ljust(typeWidth,' ')
        tmp2 = ','.join(paramTypeDim).ljust(typeWidth,' ')
        #tmp3 = ','.join(symbol.initValue).ljust(typeWidth,' ')
        tmp3 = ' '*typeWidth
        typeStr = '{0}{1}{2}{3}{4}'.format(tmp0, tmp1, tmp2, tmp3, leftOver)
        lines.append('|{0}|'.format(typeStr))
          
    return (found, lines)
    
  def statusFunctions(self, width):
    # Initialize output
    lines = []
        
    # Plot functions
    numCol = 4
    funcWidth = (width-2)/numCol
    leftOver = ' '*(width - 2 - numCol*funcWidth)
    
    # Create header
    nameStr = 'Name'.ljust(funcWidth,' ')
    paramNameStr = 'Param Name'.ljust(funcWidth,' ')
    synthStr = 'Synth?'.ljust(funcWidth,' ')
    returnStr = 'Return Type[Dim]'.ljust(funcWidth,' ')
    lines.append('-'*width)
    lines.append('|{0}|'.format('Functions'.center(width-2,' ')))
    lines.append('-'*width)
    lines.append('|{0}{1}{2}{3}{4}|'.format(nameStr, paramNameStr, synthStr, returnStr, leftOver))
    lines.append('-'*width)
    
    # List functions
    found = False
    for name,sym in self._symbol.iteritems():
      if sym[0] is 'function':
        found = True
        symbol = sym[1]
        params = symbol.returnParams()
        
        paramName = []
        for param in params:
          if param.value is None:
            paramName.append(param.name)
          else:
            paramName.append('{0}={1}'.format(param.name, param.value))
        paramTypeDim = ['{0}[{1}]'.format(param.typeName, param.typeDim) for param in params]
        
        numReturnVars = len(symbol.returnTypeName)
        returnTypeDim = ['{0}[{1}]'.format(symbol.returnTypeName[x], symbol.returnTypeDim[x]) for x in range(numReturnVars)]
        
        nameStr = symbol.name.ljust(funcWidth,' ')
        paramNameStr = ','.join(paramName).ljust(funcWidth,' ')
        synthStr = str(symbol.synth).ljust(funcWidth,' ')
        returnStr = ','.join(returnTypeDim).ljust(funcWidth,' ')
        typeStr = '{0}{1}{2}{3}{4}'.format(nameStr, paramNameStr, synthStr, returnStr, leftOver)
        lines.append('|{0}|'.format(typeStr))
          
    
    return (found, lines)
    
  def statusAttributes(self, width):
    # Initialize output
    lines = []
        
    # Plot functions
    funcWidth = (width-2)/4
    leftOver = ' '*(width - 2 - 4*funcWidth)
    
    # Create header
    nameStr = 'Name'.ljust(funcWidth,' ')
    paramNameStr = 'Param Name'.ljust(funcWidth,' ')
    paramTypeStr = 'Type[Dim]'.ljust(funcWidth,' ')
    returnStr = 'Return Type[Dim]'.ljust(funcWidth,' ')
    lines.append('-'*width)
    lines.append('|{0}|'.format('Attributes'.center(width-2,' ')))
    lines.append('-'*width)
    lines.append('|{0}{1}{2}{3}{4}|'.format(nameStr, paramNameStr, paramTypeStr, returnStr, leftOver))
    lines.append('-'*width)
    
    # List attributes
    found = False
    for name,sym in self._symbol.iteritems():
      if sym[0] is 'attr':
        found = True
        symbol = sym[1]
        params = symbol.returnParams()
        
        paramName = []
        for param in params:
          if param.value is None:
            paramName.append(param.name)
          else:
            paramName.append('{0}={1}'.format(param.name, param.value))
        paramTypeDim = ['{0}[{1}]'.format(param.typeName, param.typeDim) for param in params]
        
        numReturnVars = len(symbol.returnTypeName)
        returnTypeDim = ['{0}[{1}]'.format(symbol.returnTypeName[x], symbol.returnTypeDim[x]) for x in range(numReturnVars)]
        
        nameStr = symbol.name.ljust(funcWidth,' ')
        paramNameStr = ','.join(paramName).ljust(funcWidth,' ')
        paramTypeStr = ','.join(paramTypeDim).ljust(funcWidth,' ')
        returnStr = ','.join(returnTypeDim).ljust(funcWidth,' ')
        typeStr = '{0}{1}{2}{3}{4}'.format(nameStr, paramNameStr, paramTypeStr, returnStr, leftOver)
        lines.append('|{0}|'.format(typeStr))
          
    
    return (found, lines)
    
  def statusLibrary(self, width):
    # Initialize output
    lines = []
    
    # Plot variables
    varWidth = (width-2)/5
    leftOver = ' '*(width - 2 - 5*varWidth)
    
    # Create header
    nameStr = 'Name'.ljust(varWidth,' ')
    funcStr = 'Func.'.ljust(varWidth,' ')
    varStr = 'Var.'.ljust(varWidth,' ')
    taskStr = 'Task'.ljust(varWidth,' ')
    typeStr = 'Types'.ljust(varWidth,' ')
    lines.append('-'*width)
    lines.append('|{0}|'.format('Library'.center(width-2,' ')))
    lines.append('-'*width)
    lines.append('|{0}{1}{2}{3}{4}{5}|'.format(nameStr, funcStr, varStr, taskStr, typeStr, leftOver))
    lines.append('-'*width)
    
    # List variables
    found = False
    for name,sym in self._symbol.iteritems():
      if sym[0] is 'library':
        found = True
        symbol = sym[1]
        
        funcNum  = 0
        varNum   = 0
        taskNum  = 0
        typeNum  = 0
        for name,sym in symbol._symbol.iteritems():
          if (sym[0] is 'signal'):
            varNum += 1
          elif (sym[0] is 'function'):
            funcNum += 1
          elif (sym[0] is 'task'):
            taskNum +=1
          elif (sym[0] is 'type'):
            typeNum +=1
        
        nameStr = symbol.name.ljust(varWidth,' ')
        funcStr = str(funcNum).ljust(varWidth,' ')
        varStr = str(varNum).ljust(varWidth,' ')
        taskStr = str(taskNum).ljust(varWidth,' ')
        typeStr = str(typeNum).ljust(varWidth,' ')
        
        libStr = '{0}{1}{2}{3}{4}{5}'.format(nameStr, funcStr, varStr, taskStr, typeStr, leftOver)
        lines.append('|{0}|'.format(libStr))
        
    return (found, lines)
    
  def statusModules(self, width):
    # Initialize output
    lines = []
    
    # Plot variables
    numCol   = 4
    varWidth = (width-2)/numCol
    leftOver = ' '*(width - 2 - numCol*varWidth)
    
    # Create header
    nameStr = 'Name'.ljust(varWidth,' ')
    genStr  = 'Generic'.ljust(varWidth,' ')
    portStr = 'Ports'.ljust(varWidth,' ')
    archStr = 'Arch.'.ljust(varWidth,' ')
    
    lines.append('-'*width)
    lines.append('|{0}|'.format('Modules'.center(width-2,' ')))
    lines.append('-'*width)
    lines.append('|{0}{1}{2}{3}{4}|'.format(nameStr, genStr, portStr, archStr, leftOver))
    lines.append('-'*width)
    
    # List variables
    found = False
    for name,sym in self._symbol.iteritems():
      if sym[0] is 'module':
        found = True
        symbol = sym[1]
       
        genNum  = 0
        portNum = 0
        for name,sym in symbol._symbol.iteritems():
          if (sym[0] is 'signal'):
            if (sym[1].isPort()):
              portNum += 1
            if (sym[1].isGeneric()):
              genNum += 1
        
        nameStr = symbol.name.ljust(varWidth,' ')
        genStr  = str(genNum).ljust(varWidth,' ')
        portStr = str(portNum).ljust(varWidth,' ')
        arch = [str(x.name) for x in symbol.arch]
        archStr = str(arch).ljust(varWidth,' ')
        
        libStr = '{0}{1}{2}{3}{4}'.format(nameStr, genStr, portStr, archStr, leftOver)
        lines.append('|{0}|'.format(libStr))
        
    return (found, lines)
    
  def statusVariables(self, width):
    # Initialize output
    lines = []
    
    # Plot variables
    numCol = 5
    varWidth = (width-2)/numCol
    leftOver = ' '*(width - 2 - numCol*varWidth)
    
    # Create header
    nameStr = 'Name(Ref,Imp)'.ljust(varWidth,' ')
    portStr = 'Port/Gen(C)'.ljust(varWidth,' ')
    typeStr = 'Type'.ljust(varWidth,' ')
    val1Str = 'Init. Value'.ljust(varWidth,' ')
    val2Str = 'Asgn. Value'.ljust(varWidth,' ')
    lines.append('-'*width)
    lines.append('|{0}|'.format('Signals'.center(width-2,' ')))
    lines.append('-'*width)
    lines.append('|{0}{1}{2}{3}{4}{5}|'.format(nameStr, portStr, typeStr, val1Str, val2Str, leftOver))
    lines.append('-'*width)
    
    # List variables
    found = False
    for name,sym in self._symbol.iteritems():
      if sym[0] is 'signal':
        found = True
        symbol = sym[1]
        
        if (symbol.isParameter()):
          continue
        
        paramValue = []
        for param in symbol.typeParams:
          paramValue.append('{0}'.format(param[1]))
        paramValue = ','.join(paramValue)
        
        if (symbol.array is None):
          dimStr = '[{0}]'.format(symbol.typeDim)
        else:
          dimStr = symbol.array
        
        typeStr = '{0}({1}){2}'.format(symbol.typeName, paramValue, dimStr)
        
        nameStr = '{0}({1},{2})'.format(symbol.name, symbol.isReferenced(), symbol.isImported())
        nameStr = nameStr.replace('True','T')
        nameStr = nameStr.replace('False','F')
        nameStr = nameStr.ljust(varWidth,' ')
        if (symbol.isPort()):
          portStr = '{0}({1})'.format(symbol.portType, str(symbol.const))
        elif (symbol.isGeneric()):
          portStr = 'generic({0})'.format(str(symbol.const))
        else:
          portStr = '({0})'.format(str(symbol.const))
        portStr = portStr.replace('True','T')
        portStr = portStr.replace('False','F')
        portStr = portStr.ljust(varWidth,' ')
        typeStr = typeStr.ljust(varWidth,' ')
        val1Str = str(symbol.initValue).replace('\'','')
        val1Str = val1Str.replace('None','N')
        val1Str = val1Str.replace('\n',',').ljust(varWidth,' ')
        val2Str = str(symbol.value).replace('\'','')
        val2Str = val2Str.replace('None','N')
        val2Str = val2Str.replace('\n',',').ljust(varWidth,' ')
        typeStr = '{0}{1}{2}{3}{4}{5}'.format(nameStr, portStr, typeStr, val1Str, val2Str, leftOver)
        lines.append('|{0}|'.format(typeStr))
        
    return (found, lines)
    
