from Lexer import Lexer
from Parser import Parser
import yaml

def main():
  #Load Lexer Configuration
  fo = open('grammer-fdl.yaml')
  lexerConfig = yaml.load(fo.read())
  fo.close()
  
  #Test String
  fo = open('simple.fdl')
  testStr = fo.read()
  fo.close()
  
  #Initialize Lexer
  lexer   = Lexer(testStr, lexerConfig)
  parser  = Parser(lexer)
  
  # Build AST
  ast = parser.parse()
  
  importNodes = ast.importNodes
  
  print('\nImport')
  for node in importNodes:
    print(node)
    
  moduleNode = ast.moduleNode
  print('\n')
  print('Module "{0}"'.format(moduleNode.name))
  print('Generics\n')
  for node in moduleNode.genDeclNodes:
    print(node)
  print('Ports\n')
  for node in moduleNode.portDeclNodes:
    print(node)
  archNode = moduleNode.archNode
  print('Architecture "{0}"'.format(archNode.name))
  print('Signal Scope {0}\n'.format(archNode.signalScope))
  for node in archNode.sigDeclNodes:
    print(node)
  print('Logic Scope {0}\n'.format(archNode.logicScope))
  for node in archNode.statements:
    print(node)
    print('Args\n')
    for arg in node.args:
      print(arg.left.left)
    print('Statements {0}\n'.format(len(node.statements)))
    for state in node.statements:
      print(state.leftVar)
      print(state.rightExpr.left.left)
    
    
if __name__ == '__main__':
  main()
