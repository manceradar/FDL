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
    width = 104
    header = '|{0}|'.format('Scope Symbol Table'.center(width-2,' '))
    scopeDetail = '|{0}|'.format('Name: "{0}", Scope: {1}'.format(self.scopeName, self.scopeLevel).center(width-2,' '))
    lines = ['=' * width, header, scopeDetail]
    print('\n'.join(lines))
    
    self.statusTypes(width)
    self.statusFunctions(width)
    self.statusAttributes(width)
      
    lines = []
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
    # Create header
    header = 'Types'
    nameList = ['Name']
    paramNameList = ['Param Name']
    paramTypeList = ['Param Type[Dim]']
    paramInitList = ['Default Value']
    
    # List types
    found = False
    for name,sym in self._symbol.iteritems():
      if sym[0] is 'type':
        found = True
        symbol = sym[1]
        params = symbol.returnParams()
        paramName = [param.name for param in params]
        paramTypeDim = ['{0}[{1}]'.format(param.typeName, param.typeDim) for param in params]
        paramValue = [str(param.value) for param in params]
        nameList.append(symbol.name)
        paramNameList.append(','.join(paramName))
        paramTypeList.append(','.join(paramTypeDim))
        paramInitList.append(','.join(paramValue))
        
    tableLines = self.formatTable(header, width, nameList, paramNameList, 
                                  paramTypeList, paramInitList)
          
    if (found):
      print('\n'.join(tableLines))
    
  def statusFunctions(self, width):
    # Create header
    header = 'Functions'
    nameList = ['Name']
    paramNameList = ['Param Name']
    paramTypeList = ['Param Type[Dim]']
    synthList = ['Synth?']
    returnList = ['Return Type[Dim]']
    
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
        
        nameList.append(symbol.name)
        paramNameList.append(','.join(paramName))
        paramTypeList.append(','.join(paramTypeDim))
        synthList.append(str(symbol.synth))
        returnList.append(','.join(returnTypeDim))
        
    tableLines = self.formatTable(header, width, nameList, paramNameList, 
                                  paramTypeList, synthList, returnList)
    
    if (found):
      print('\n'.join(tableLines))
    
  def statusAttributes(self, width):
    # Create header
    header = 'Attributes'
    nameList = ['Name']
    paramNameList = ['Param Name']
    paramTypeList = ['Param Type[Dim]']
    returnList = ['Return Type[Dim]']
    
    # List functions
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
        
        nameList.append(symbol.name)
        paramNameList.append(','.join(paramName))
        paramTypeList.append(','.join(paramTypeDim))
        returnList.append(','.join(returnTypeDim))
        
    tableLines = self.formatTable(header, width, nameList, paramNameList, 
                                  paramTypeList, returnList)
    
    if (found):
      print('\n'.join(tableLines))
    
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
    
  def formatLine(self, maxColLen, tableLeftOver, ind, args):
    # Create Line
    line = ''
    for x in range(len(args)):
      leftOver = maxColLen[x]-len(args[x][ind])-2
      line += '| {0}{1} '.format(args[x][ind],' '*leftOver)
    line += '{0}|'.format(' '*tableLeftOver)
    
    return line

  def formatTable(self, header, maxTableWidth, *args):
    # Constants
    numCol = len(args)
    
    if not all([len(x)==len(args[0]) for x in args]):
      raise Exception('FormatTable: All columns not same size')
    
    # Maximum length of all columns
    maxlenCol = []
    for arg in args:
      lenList = [len(x) for x in arg]
      maxlenCol.append(max(lenList)+2)
      
    # Leftover space in table
    tableLeftOver = maxTableWidth- (sum(maxlenCol) + numCol + 1)
    
    # Determine table width
    if tableLeftOver<0:
      raise Exception('FormatTable: Console not big enough')
    
    outerSepLine = '|'+'='*(maxTableWidth-2)+'|'
    innerSepLine = '|'+'-'*(maxTableWidth-2)+'|'
    headerLine = '|{0}|'.format(header.center(maxTableWidth-2,' '))
    
    # Create table
    tableLines = []
    tableLines.append(outerSepLine)
    tableLines.append(headerLine)
    tableLines.append(innerSepLine)
    tableLines.append(self.formatLine(maxlenCol, tableLeftOver, 0, args))
    tableLines.append(innerSepLine)
    for ind in range(1,len(args[0])):
      tableLines.append(self.formatLine(maxlenCol, tableLeftOver, ind, args))
    
    return tableLines
