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
  parser.parse()
    
    
if __name__ == '__main__':
  main()
