from collections import OrderedDict

from Lexer import Token

class SymbolTable (object):
  def __init__(self,scopeName,scopeLevel,enclosingScope):
    # Initialize symbol table, it is list inside a dict.
    # The outer dict checks for symbol name, and inner list
    # has what that symbol means. 
    self._symbol        = OrderedDict()
    self.scopeName      = scopeName
    self.scopeLevel     = scopeLevel
    self.enclosingScope = enclosingScope
    
    # Being inside implementation allows to replace Self with actual value
    if enclosingScope is None:
      self.impl        = False
    else:
      self.impl        = enclosingScope.impl
      
    # Being inside trait do not evaluate func/task definitions
    if enclosingScope is None:
      self.trait       = False
    else:
      self.trait       = enclosingScope.trait
      
    # Being inside module allows full type and array checks
    if enclosingScope is None:
      self.module       = False
    else:
      self.module       = enclosingScope.module
    
  # Used to determine if implemntation being used to convert types
  def setImpl(self, value):
    self.impl = value
    
  # Used to limit type checks in traits
  def setTrait(self, value):
    self.trait = value
    
  def setModule(self, value):
    self.module = value
       
  def insert(self, symbol, lookupCheck=True):
    # Inserts symbol into table, and checks for replicas
    # Returns bool if it was inserted
    
    # Look up symbol name
    lookupSym = None
    
    # Dont check for imports
    if lookupCheck:
      lookupSym = self.lookup(symbol.name, symbol.type, printError=False)
    
    # Add symbol
    if (lookupSym is None):
      self._symbol[symbol.name] = (symbol.type, symbol)
      print('insert:T({0},{1})'.format(symbol.name, symbol.type))
      return True
    else:
      print('insert:F({0},{1})'.format(symbol.name, symbol.type))
      return False
      
    
  def lookup(self, name, type, recursive=True, printError=True):
    # If Token, get value to lookup
    if isinstance(name, Token):
      nameStr = name.value
    else:
      nameStr = name
      
    # Look for type in current scope
    symbolList = self._symbol.get(nameStr)
    
    if (symbolList is None):
      # Symbol not found, look in enclosing scope
      if (self.enclosingScope is None):
        # All scopes didnt find type
        if (printError):
          print('Symbol Name "{0}", Type "{1}" not found'.format(nameStr, type))
        return None
      else:
        if recursive:
          return self.enclosingScope.lookup(nameStr, type, printError=printError)
        else:
          return None
        
    else:
      # Symbol found, check if type exists
      if (isinstance(type, str)):
        if (type == 'all'):
          return symbolList[1]
        elif (type == symbolList[0]):
          # Return symbol for index
          return symbolList[1]
        else:
          # Correct symbol name, wrong type
          # Symbol not found, look in enclosing scope
          if (self.enclosingScope is None):
            # All scopes didnt find type
            if (printError):
              print('Symbol Name "{0}", Type "{1}" not found'.format(nameStr, type))
            return None
          else:
            if recursive:
              return self.enclosingScope.lookup(nameStr, type, printError=printError)
            else:
              return None
          
      elif (isinstance(type, list)):
        if (symbolList[0] in type):
          # Symbol name and type match, return symbol
          return symbolList[1]
        else:
          # Correct symbol name, wrong type
          # Symbol not found, look in enclosing scope
          if (self.enclosingScope is None):
            # All scopes didnt find type
            if (printError):
              print('Symbol Name "{0}", Type "{1}" not found'.format(nameStr, type))
            return None
          else:
            if recursive:
              return self.enclosingScope.lookup(nameStr, type, printError=printError)
            else:
              return None
              
  def returnSymbolList(self, typeLookup):
    symList = []
    for name,sym in iter(self._symbol.items()):
      if (sym[0] in typeLookup):
        symList.append(sym[1])
          
    return symList
        
  def returnParams(self):
    params = []
    for name,sym in iter(self._symbol.items()):
      if (sym[1].isParameter()):
        params.append(sym[1])
          
    return params
    
  def removeImports(self):
    # Look for all imports and remove them
    for name,sym in iter(self._symbol.items()):
      if (sym[1].isImported()):
        del self._symbol[name]
        
  def status(self):
    # Plot header
    width = 120
    header = '|{0}|'.format('Scope Symbol Table'.center(width-2,' '))
    scopeDetail = '|{0}|'.format('Name: "{0}", Scope: {1}'.format(self.scopeName, self.scopeLevel).center(width-2,' '))
    lines = ['=' * width, header, scopeDetail]
    print('\n'.join(lines))
    
    #self.statusFile(width)
    self.statusTypes(width)
    self.statusGenerics(width)
    self.statusFunctions(width)
    self.statusAttributes(width)
    self.statusLibrary(width, 'library')
    self.statusLibrary(width, 'trait')
    self.statusModules(width)
    self.statusVariables(width)
      
    lines = []
    lines.append('='*width)
    lines.append('')
    print('\n'.join(lines))
    
  def statusFile(self, width):
    # Initialize output
    lines = []
    
    # Plot variables
    numVars = 7
    varWidth = int((width-2)/numVars)
    leftOver = ' '*int(width - 2 - numVars*varWidth)
    
    # Create header
    nameStr = 'Name'.ljust(varWidth,' ')
    libStr = 'Lib.'.ljust(varWidth,' ')
    traitStr = 'Trait'.ljust(varWidth,' ')
    funcStr = 'Func.'.ljust(varWidth,' ')
    varStr = 'Var.'.ljust(varWidth,' ')
    taskStr = 'Task'.ljust(varWidth,' ')
    typeStr = 'Types'.ljust(varWidth,' ')
    lines.append('-'*width)
    lines.append('|{0}|'.format('File'.center(width-2,' ')))
    lines.append('-'*width)
    lines.append('|{0}{1}{2}{3}{4}{5}{6}{7}|'.format(nameStr, libStr, traitStr, funcStr, varStr, taskStr, typeStr, leftOver))
    lines.append('-'*width)
    
    # List variables
    libNum   = 0
    traitNum = 0
    funcNum  = 0
    varNum   = 0
    taskNum  = 0
    typeNum  = 0
    for name,sym in iter(self._symbol.items()):
      found = True
      symbol = sym[1]
      
      for name,sym in iter(symbol._symbol.items()):
        if (sym[0] is 'signal'):
          varNum += 1
        elif (sym[0] is 'trait'):
          traitNum += 1
        elif (sym[0] is 'library'):
          libNum += 1
        elif (sym[0] is 'function'):
          funcNum += 1
        elif (sym[0] is 'task'):
          taskNum +=1
        elif (sym[0] is 'type'):
          typeNum +=1
      
    nameStr = symbol.name.ljust(varWidth,' ')
    libStr = str(libNum).ljust(varWidth,' ')
    traitStr = str(traitNum).ljust(varWidth,' ')
    funcStr = str(funcNum).ljust(varWidth,' ')
    varStr = str(varNum).ljust(varWidth,' ')
    taskStr = str(taskNum).ljust(varWidth,' ')
    typeStr = str(typeNum).ljust(varWidth,' ')
    
    libStr = '{0}{1}{2}{3}{4}{5}{6}{7}'.format(nameStr, libStr, traitStr, funcStr, varStr, taskStr, typeStr, leftOver)
    lines.append('|{0}|'.format(libStr))
        
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
    for name,sym in iter(self._symbol.items()):
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
      
  def statusGenerics(self, width):
    # Create header
    header = 'Generics'
    nameList = ['Name']
    boundList = ['Type Bounds']
    defaultList = ['Default Type']
    
    # List types
    found = False
    for name,sym in iter(self._symbol.items()):
      if sym[0] is 'generic':
        found = True
        symbol = sym[1]
        boundListStr = ['{0}'.format(bound) for bound in symbol.typeBound]
        nameList.append(symbol.name)
        boundList.append(','.join(boundListStr))
        defaultList.append(str(symbol.defaultType))
        
    tableLines = self.formatTable(header, width, nameList, boundList, defaultList)
          
    if (found):
      print('\n'.join(tableLines))
    
  def statusFunctions(self, width):
    # Create header
    header = 'Functions'
    nameList = ['Name']
    paramNameList = ['Param Name']
    paramTypeList = ['Param Type[Dim]']
    defList = ['Definition']
    returnList = ['Return Type[Dim]']
    
    # List functions
    found = False
    for name,sym in iter(self._symbol.items()):
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
        defList.append(str(symbol.funcDef))
        returnList.append(','.join(returnTypeDim))
        
    tableLines = self.formatTable(header, width, nameList, paramNameList, 
                                  paramTypeList, defList, returnList)
    
    if (found):
      print('\n'.join(tableLines))
    
  def statusAttributes(self, width):
    # Create header
    header = 'Attributes'
    nameList = ['Name']
    valueList = ['Value']
    typeList = ['Type']
    
    # List functions
    found = False
    for name,sym in iter(self._symbol.items()):
      if sym[0] is 'attr':
        found = True
        symbol = sym[1]
        
        nameList.append(symbol.name)
        valueList.append(symbol.value.value)
        typeList.append(symbol.attrType)
        
    tableLines = self.formatTable(header, width, nameList, valueList, typeList)
    
    if (found):
      print('\n'.join(tableLines))
    
  def statusLibrary(self, width, symName):
    # Initialize output
    lines = []
    
    # Plot variables
    numVars = 7
    varWidth = int((width-2)/numVars)
    leftOver = ' '*int(width - 2 - numVars*varWidth)
    
    # Create header
    nameStr = 'Name'.ljust(varWidth,' ')
    libStr = 'Lib.'.ljust(varWidth,' ')
    traitStr = 'Trait'.ljust(varWidth,' ')
    funcStr = 'Func.'.ljust(varWidth,' ')
    varStr = 'Var.'.ljust(varWidth,' ')
    taskStr = 'Task'.ljust(varWidth,' ')
    typeStr = 'Types'.ljust(varWidth,' ')
    lines.append('-'*width)
    lines.append('|{0}|'.format(symName.center(width-2,' ')))
    lines.append('-'*width)
    lines.append('|{0}{1}{2}{3}{4}{5}{6}{7}|'.format(nameStr, libStr, traitStr, funcStr, varStr, taskStr, typeStr, leftOver))
    lines.append('-'*width)
    
    # List variables
    found = False
    for name,sym in iter(self._symbol.items()):
      if sym[0] is symName:
        found = True
        symbol = sym[1]
        
        libNum   = 0
        traitNum = 0
        funcNum  = 0
        varNum   = 0
        taskNum  = 0
        typeNum  = 0
        for name,sym in iter(symbol._symbol.items()):
          if (sym[0] is 'signal'):
            varNum += 1
          elif (sym[0] is 'trait'):
            traitNum += 1
          elif (sym[0] is 'library'):
            libNum += 1
          elif (sym[0] is 'function'):
            funcNum += 1
          elif (sym[0] is 'task'):
            taskNum +=1
          elif (sym[0] is 'type'):
            typeNum +=1
        
        nameStr = symbol.name.ljust(varWidth,' ')
        libStr = str(libNum).ljust(varWidth,' ')
        traitStr = str(traitNum).ljust(varWidth,' ')
        funcStr = str(funcNum).ljust(varWidth,' ')
        varStr = str(varNum).ljust(varWidth,' ')
        taskStr = str(taskNum).ljust(varWidth,' ')
        typeStr = str(typeNum).ljust(varWidth,' ')
        
        libStr = '{0}{1}{2}{3}{4}{5}{6}{7}'.format(nameStr, libStr, traitStr, funcStr, varStr, taskStr, typeStr, leftOver)
        lines.append('|{0}|'.format(libStr))
        
    if (found):
      print('\n'.join(lines))
    
  def statusModules(self, width):
    # Initialize output
    lines = []
    
    # Plot variables
    numCol   = 4
    varWidth = int((width-2)/numCol)
    leftOver = ' '*int(width - 2 - numCol*varWidth)
    
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
    for name,sym in iter(self._symbol.items()):
      if sym[0] is 'module':
        found = True
        symbol = sym[1]
       
        genNum  = 0
        portNum = 0
        for name,sym in iter(symbol._symbol.items()):
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
        
    if (found):
      print('\n'.join(lines))
    
  def statusVariables(self, width):
    
    # Create header
    header   = 'Signals'
    nameList = ['Name(Ref,Imp)']
    portList = ['Port/Gen(C)']
    typeList = ['Type']
    val1List = ['Value']
    val2List = ['Used']
    val3List = ['Init.']
    
    # List variables
    found = False
    for name,sym in iter(self._symbol.items()):
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
          dimStr = str(symbol.array)
          
        if (type(symbol) is not str):
          typeName = '.'.join(symbol.typeName)
        else:
          typeName = symbol.typeName
        
        typeStr = '{0}({1}){2}'.format(typeName, paramValue, dimStr)
        
        nameStr = '{0}({1},{2})'.format(symbol.name, symbol.isReferenced(), symbol.isImported())
        nameStr = nameStr.replace('True','T')
        nameStr = nameStr.replace('False','F')
        
        if (symbol.isPort()):
          portStr = '{0}({1})'.format(symbol.portType, str(symbol.const))
        elif (symbol.isGeneric()):
          portStr = 'generic({0})'.format(str(symbol.const))
        else:
          portStr = '({0})'.format(str(symbol.const))
        portStr = portStr.replace('True','T')
        portStr = portStr.replace('False','F')
        portStr = portStr
        
        typeStr = typeStr
        
        val1Str = str(symbol.value).replace('\'','')
        val1Str = val1Str.replace('None','N')
        val1Str = val1Str.replace('\n',',')
        
        val2Str = str(symbol.valAsgnd)
        val2Str = val2Str.replace('True','T')
        val2Str = val2Str.replace('False','F')
        val2Str = val2Str.replace(' ','')
        
        val3Str = str(symbol.initAsgnd)
        val3Str = val3Str.replace('True','T')
        val3Str = val3Str.replace('False','F')
        val3Str = val3Str.replace(' ','')
        
        nameList.append(nameStr)
        portList.append(portStr)
        typeList.append(typeStr)
        val1List.append(val1Str)
        val2List.append(val2Str)
        val3List.append(val3Str)
        
    tableLines = self.formatTable(header, width, nameList, portList, 
                                  typeList, val1List, val2List,val3List)
        
    if (found):
      print('\n'.join(tableLines))
    
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
