from Lexer import Lexer
from Parser import Parser
from SemanticAnalyzer import SemanticAnalyzer
from Convert import Convert
import yaml
import os

def main():
  #Load Lexer Configuration
  fo = open('grammer-fdl.yaml')
  gramConfig = yaml.load(fo.read())
  fo.close()
  
  #Test String
  fdl_filename = 'simple.fdl'
  fo = open(fdl_filename)
  testStr = fo.read()
  fo.close()
  
  #Initialize Lexer
  lexer   = Lexer(testStr, gramConfig)
  parser  = Parser(lexer)
  
  # Build AST
  ast = parser.parse()
  
  # Walk tree
  #base, ext = os.path.splitext(fdl_filename)
  #vhdlFilename = base + '.vhd'
  #walker = SemanticAnalyzer(vhdlFilename, gramConfig)
  #walker.visit(ast)
  
  
if __name__ == '__main__':
  main()
