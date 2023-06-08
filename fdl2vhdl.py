

import sys,os

fdlPath = sys.path[0]
sys.path.append(fdlPath + ('/fdl/'))

import fdl
import yaml

# Display Pythonista console better
try:
  import console
  console.set_font("Menlo-Regular", 10)
except ImportError:
  pass

def main(project_files, project_path):
  #Load Lexer Configuration
  fo = open('builtin/test.yaml')
  #print(fo.read())
  gramConfig = yaml.load(fo.read())
  fo.close()
  print(gramConfig)
  
  #FDL source files
  fdl_filename_list = [
    ('builtin/std/std.fdl', ['std']),
    ]
    
  # Add project files
  project_files_import = [(x, None) for x in project_files]
  fdl_filename_list.extend(project_files_import)
  
  # FDL standard library path
  fdl_stdlib_path = ['builtin/']
  
  #Initialize Lexer/SyntaxParser
  lexer   = fdl.Lexer(gramConfig)
  parser  = fdl.SyntaxParser(lexer)
  
  # Build Semantic Analyzer and Symbol Table
  semAnalyzer = fdl.SemanticAnalyzer(gramConfig, fdl_stdlib_path)
  semAnalyzer.addPath(project_path)
                       
  # Build AST
  astList = []
  for (fdl_filename, importName) in fdl_filename_list:
    #Read FDL file
    fo = open(fdl_filename)
    fdlStr = fo.read()
    fo.close()
    
    # Append AST
    ast = parser.parse(fdlStr, fdl_filename, importName)
    
    #print('\n'.join(ast.log()))
  
    # Check semantics
    addedFiles = semAnalyzer.pre_process(ast)
    fdl_filename_list.extend(addedFiles)
    
  # Now process AST
  semAnalyzer.process()
  
if __name__ == '__main__':
  
  project_files = [
    'examples/VariableDelay.fdl'
    ]
  
  project_path = [
    'examples/'
    ]
  main(project_files, project_path)
