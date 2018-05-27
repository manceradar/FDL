from NodeVisitor import NodeVisitor

def addScope(origStr,scope):
  strList = origStr.splitlines()
  for ind,line in enumerate(strList):
    strList[ind] = '  '*scope + line
    
  return '\n'.join(strList)

class Convert (NodeVisitor):
  def __init__(self, filename, config):
    self.fid = open(filename,'w')
    self.config = config
    self.fid.write(config['fdlHeader'])
    self.fid.write(config['vhdlHeader'])
    
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
    genDecl = []
    genLen = 0
    for gen in node.genDeclNodes:
      genDecl.append(self.visit(gen))
      genLen = max(genLen, len(genDecl[-1][1]))
      
    portDecl = []
    portLen = 0
    for port in node.portDeclNodes:
      portDecl.append(self.visit(port))
      portLen = max(portLen, len(portDecl[-1][1]))
      
    # write generics declaration
    genStr = ''
    for gen in genDecl:
      name = gen[1].ljust(genLen,' ')
      if gen[4]:
        genStr += '  {0} : {1} := \'{2}\';\n'.format(name,gen[2],gen[4])
      else:
        genStr += '  {0} : {1};\n'.format(name,gen[2])
      
    # only write formatted generics if there are any
    if (len(genStr) > 0):
      # Trim off EOL and comma
      genStr = genStr[0:-2]
      # Write formatted generics
      genStr = self.config['generics'].format(genStr)
      genStr = addScope(genStr,1)
      genStr += '\n'
      
    # write ports decl.
    portStr = ''
    for port in portDecl:
      pName = port[1].ljust(portLen,' ')
      pPort = port[3].ljust(4,' ')
      pType = port[2]
      portStr += '  {0} : {1}{2};\n'.format(pName,pPort,pType)
      
    # Trim off EOL and selicolon
    portStr = portStr[0:-2]
    
    # write formatted ports decl.
    portStr = self.config['ports'].format(portStr)
    portStr = portStr[0:-1]
    portStr = addScope(portStr,1)
      
    # Write module ports
    entityStr = '{0}{1}'.format(genStr,portStr)
    moduleStr = self.config['module'].format(node.name, entityStr)
    self.fid.write('\n\n')
    self.fid.write(moduleStr)
    self.fid.write('\n')
      
    self.visit(node.archNode)
    
  def visit_archblock(self, node):
    # Loop over signal declarations
    sigDecl = []
    sigLen = 0
    for sig in node.sigDeclNodes:
      sigDecl.append(self.visit(sig))
      sigLen = max(sigLen, len(sigDecl[-1][1]))
      
    # write generics declaration
    sigStr = ''
    for sig in sigDecl:
      sName = sig[1].ljust(sigLen,' ')
      sType = sig[2]
      if sig[4]:
        sigStr += '  signal {0} : {1} := \'{2}\';\n'.format(sName,sType,sig[4])
      else:
        sigStr += '  signal {0} : {1};\n'.format(sName,sType)
      
    sigStr = sigStr[0:-1]
      
    # Loop through statements
    smStr = ''
    for sm in node.statements:
      smStr += self.visit(sm)
      
    smStr = smStr[0:-1]
    
    archName = node.name
    entityName = node.entity
    archStr = self.config['arch'].format(archName, entityName, sigStr, smStr)
    self.fid.write(archStr)
    
      
  def visit_decl(self,node):
    # Check declarations
    return (node.const, node.name, 'std_logic', node.port, node.value)
      
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
    
    return '  {0} <= {1};\n'.format(leftVar, rightExpr)
      
  def visit_expr(self,node):
    # First visit node to verify it
    # Validate 'left'
    left = self.visit(node.left)
    op = node.op
    right = self.visit(node.right)
    
    print(left.__str__(),right.__str__())
    
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
    print(result.__str__())
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
    
    return node.name
      
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
