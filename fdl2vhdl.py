from Lexer import Lexer
from Parser import Parser
from SemanticAnalyzer import SemanticAnalyzer
import yaml

def main():
  #Load Lexer Configuration
  fo = open('grammer-fdl.yaml')
  gramConfig = yaml.load(fo.read())
  fo.close()
  
  #Test String
  fo = open('simple.fdl')
  testStr = fo.read()
  fo.close()
  
  #Initialize Lexer
  lexer   = Lexer(testStr, gramConfig)
  parser  = Parser(lexer)
  
  # Build AST
  ast = parser.parse()
  
  # Walk tree
  walker = SemanticAnalyzer(gramConfig['syntax']['types'])
  walker.visit(ast)
  
if __name__ == '__main__':
  main()
