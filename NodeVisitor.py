class NodeVisitor (object):
  def visit(self, node):
    methodname = 'visit_' + node.base.lower()
    visitor = getattr(self, methodname, self.visit_error)
    return visitor(node)
    
  def visit_error(self, node):
    print('Visit Error: No visitor for type "{0}"'.format(node.base))
