import fdl
import yaml
import os

# Display Pythonista console better
try:
  import console
  console.set_font("Menlo-Regular", 10)
except ImportError:
  pass

def main():
  #Load Lexer Configuration
  fo = open('builtin/grammer-fdl.yaml')
  gramConfig = yaml.load(fo.read())
  fo.close()
  
  #FDL source files
  fdl_filename_list = ['examples/VariableDelay.fdl',
                       'examples/func_task.fdl',]
                       
  # Build AST
  astList = []
  for fdl_filename in fdl_filename_list:
    #Read FDL file
    fo = open(fdl_filename)
    fdlStr = fo.read()
    fo.close()
    
    #Initialize Lexer/SyntaxParser
    lexer   = fdl.Lexer(fdlStr, gramConfig)
    parser  = fdl.SyntaxParser(lexer)
    
    # Append AST
    astList.append(parser.parse())
  
  # Print AST for debugging
  for ast in astList:
    print('\n'.join(ast.log()))
  
  # Check semantics
  #semAnalyzer = fdl.SemanticAnalyzer(gramConfig, astList[0:1])
  #semAnalyzer.process(astList[1:])
  
if __name__ == '__main__':
  main()
