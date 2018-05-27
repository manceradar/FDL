from Lexer import Lexer
from SyntaxParser import SyntaxParser
from SemanticAnalyzer import SemanticAnalyzer
import yaml
import os

# Display Pythonista console better
try:
  import console
  console.set_font("Menlo-Regular", 12)
except ImportError:
  pass

def main():
  #Load Lexer Configuration
  fo = open('grammer-fdl.yaml')
  gramConfig = yaml.load(fo.read())
  fo.close()
  
  #FDL source files
  fdl_filename_list = ['std_logic_1164.fdl',
                       'expr.fdl',
                       'VariableDelay.fdl', 
                       'TopLevel.fdl']
                       
  # Build AST
  astList = []
  for fdl_filename in fdl_filename_list:
    #Read FDL file
    fo = open(fdl_filename)
    fdlStr = fo.read()
    fo.close()
    
    #Initialize Lexer/SyntaxParser
    lexer   = Lexer(fdlStr, gramConfig)
    parser  = SyntaxParser(lexer)
    
    # Append AST
    astList.append(parser.parse())
  
  # Print AST for debugging
  for ast in astList[1:]:
    print('\n'.join(ast.log()))
  
  # Check semantics
  semAnalyzer = SemanticAnalyzer(gramConfig, astList[0:1])
  semAnalyzer.process(astList[1:])
  
if __name__ == '__main__':
  main()
