class NodeVisitor (object):
  def visit(self, node):
    methodname = 'visit_' + node.base.lower()
    visitor = getattr(self, methodname, self.visit_error)
    return visitor(node)
    
  def visit_error(self, node):
    print('Visit Error: No visitor for type "{0}"'.format(node.base))
    
  def compile(self, node):
    methodname = 'compiler_' + node.base.lower()
    compiler = getattr(self, methodname, self.compile_error)
    return compiler(node)
    
  def compile_error(self, node):
    print('Compile Error: No compiler for type "{0}"'.format(node.base))
