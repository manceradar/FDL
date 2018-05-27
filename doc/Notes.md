# Overall Language Construct

This document covers how the FPGA Description Language (FDL, pronounced "Fiddle") language is constructed and how the compiler works.

## Language structure

The language has been designed to follow the VHDL structure for libraries and 
module definitions. The FDL language extends the language to support parameterized 
records, in addition to introducing the interface data structure. The testbench 
construct is defined in a more formalized way to included specific testbench 
features. Some of these features include only being able to have 'wait' in testbench
construct and none in modules or functions, a dedicated testbench architecture,
builtin testbench functions, and easier reporting a status.

Due to industry tools not supporting new features of VHDL, FDL uses the supported
features of each tool to make more readable code in fewer lines. 

### Data Types

FDL has the builtin data types commonly seen in VHDL. Note that all data types 
are derived from the "bit" data type.

| Data Type | Allowed Values | Example Variable Declaration |
| --------- | -------------- | ---------------------------- |
| bit       | '0','1','Z','X','L','H','-' | `bit foo = '1'` |
| bool | True, False | `bool foo = False` |
| sint(uint numBits = 32) | integer | `uint(8) foo = 100` |
| uint(uint numBits = 32) | integer | `sint foo = -100` |
| float | float | `float foo = 3.14` |
| str | string | `str foo = "Data ready!\n"` |
| enum | string | `enum foo = {stReady, stRead, stWrite, stWait}` |
| time | float, integer | `time foo = 4 ns` |
| freq | float, integer | `freq foo = 100 MHz` |

FDL also extends the language for allow for data consolidation using records/structs
and interfaces. Most of the tools don't support these features, but FDL expands the
variables behind the scenes such that the tools are happy.

The structure data type allows for data consolidation when all the ports are going
in one direction.

```
struct complex(uint numBits):
  sint(numBits) real
  sint(numBits) imag
  bit           valid
```

There interface data type is very similar to the structure data type, but allows the 
user to define the direction of the underlying data with the view feature. TODO: How does view work?

### Data Arrays

FDL handles arrays differently than VHDL. Instead of unique data types for each 
array size, arrays are handled like C. FDL allows the user to extend any data type
automatically. Additionally, arrays can be assign using curly braces.

```
# 1 dimensional array
sint(8)[1:0] = {4, 5}
# 2 dimensional array
uint[0:3][0:1] = {{1,2}, {3,4}, {5,6}, {7,8}}
```

For function calls, the data array dimension needs to be specified by using the '*' 
character. The dimension size doesn't need to be known, but can be determined in the
function.

```
# and function with two, one dimensional 'bit' inputs
function and(bit* left, bit* right):
```

### Modules

Modules are defined similarly to VHDL. A module is equivalent to an entity in VHDL.
There is an optional generic and required port declaration for modules. Generics
can have default values, but not required. Module instances must have all generic
values defined either through assignment or default values. An example of a module
named 'Test' with one generic and three ports.

```
module Test:
  generics:
    sint blah = 1
  ports:
    bit  in  CLK
    bit  in  A
    bit  out B
```

### Libraries

### Testbenches

Tasks are defined in libraries.
Routines are defined in testbenches.

## FPGA Descriptor Language Compiler

### Lexical Analysis

The Lexer is responsible for taking a string from a .fdl file and convert it to a 
list of tokens. The tokens are determined from the grammar-fdl.yaml configuration
file. The tokens are found through regular expressions to the end of the line. Each
token is found in order for proper parsing. The exception comes in the ID token, 
where before it's assign an ID it is checked to be a keyword. FDL has the following keywords:

| FDL Keywords ||||
|--------------||||
| import | library | function | enum |
| module | blackbox | generics | ports |
| in | out | inout | master |
| slave | arch | declare | logic |
| rename | for | case | struct |
| interface | const | others | pro |
| spro | apro | if | elif |
| else | return | assert | print |
| warning | error | delay | until |
| on | task | single | repeat |
| while | routine | open | not |
| attr | next | exit |  |
| and | or | nand | nor |
| xor | xnor | sll | srl |
| sla | sra | ror | rol |
| mod | rem |||

### Syntax Parsing

Syntax parsing rules follow regular expression rules

* '*' means to match zero or more occurances
* '(FOO | BAR)' means to match FOO or BAR
* '?' means to match zero or one occurance
* '+' means to match one or more occurances

```
FILE = (IMPORT_STMT|LIB_DECL|MODULE_DECL|TESTBENCH_DECL)

IMPORT_STMT = IMPORT ID (DOT ID)?

LIB_DECL = LIBRARY ID COLON
LIB_BLOCK = (FUNC_DECL|TASK_DECL|STRUCT_DECL|INTERFACE_DECL|VAR_DECL|ENUM_DECL)

STRUCT_DECL = STRUCT ID (DECL_ARG_LIST)? COLON
STRUCT_FIELD = TYPE (CALL_ARG_LIST)? (INDEX_LIST)? ID

INTERFACE_DECL = INTERFACE ID (DECL_ARG_LIST)? COLON
INTERFACE_FIELD = TYPE (CALL_ARG_LIST)? (INDEX_LIST)? BASE_INTERFACE ID

FUNC_DECL = FUNCTION (ID|OPERATORS) DECL_ARG_LIST COLON

TASK_DECL = TASK ID COLON
TASK_PORT = PORTS COLON
TASK_PORT_DECL = TYPE (STAR)* (BASE_INTERFACE|EXT_INTERFACE|ID) ID

DECL_ARG_LIST = LPAREN DECL_ARG (COMMA DECL_ARG)* RPAREN
DECL_ARG = TYPE (STAR)* ID

CALL_ARG_LIST = LPAREN SIMP_EXPR (COMMA SIMP_EXPR)* RPAREN

MODULE_DECL = MODULE ID (LPAREN BLACKBOX RPAREN)? COLON
MODULE_GENERIC = (GENERICS COLON)?
MODULE_PORTS = (PORTS COLON)?

GEN_DECL = TYPE (CALL_ARG_LIST)? (INDEX_LIST)? ID (ASSIGN CMPX_EXPR)?
PORT_DECL = TYPE (CALL_ARG_LIST)? (INDEX_LIST)? (BASE_INTERFACE|EXT_INTERFACE|ID) ID
VAR_DECL = (CONSTANT)? TYPE (CALL_ARG_LIST)? (INDEX_LIST)? ID (ASSIGN CMPX_EXPR)?
TYPE = ID

ARCH_DECL = ARCH ID LPAREN ID RPAREN COLON
ARCH_DECLARE = DECLARE COLON
ARCH_LOGIC = LOGIC COLON
DECLARE_BLOCK = (FUNC_DECL|STRUCT_DECL|INTERFACE_DECL|VAR_DECL|ENUM_DECL)

TESTBENCH_DECL = TESTBENCH ID COLON
TESTBENCH_GENERIC = (GENERICS COLON)?
TESTBENCH_DECLARE = (FUNC_DECL|TASK_DECL|STRUCT_DECL|INTERFACE_DECL|VAR_DECL|ENUM_DECL)
TESTBENCH_LOGIC = (ASSIGNMENT|FORBLOCK|CASEBLOCK|IFBLOCK|ASSERTION|PROBLOCK|MODULE_INST|ROUTINE_BLOCK|TASK_CALL)

ARCH_STATEMENTS = (ASSIGNMENT|FORBLOCK|CASEBLOCK|IFBLOCK|ASSERTION|PROBLOCK|MODULE_INST|RENAME_STMT)
FUNC_STATEMENTS = (ASSIGNMENT|FORBLOCK|CASEBLOCK|IFBLOCK|ASSERTION|REPORT|RETURN_STMT)
TASK_STATEMENTS = (ASSIGNMENT|FORBLOCK|CASEBLOCK|IFBLOCK|ASSERTION|REPORT|DELAY_STMT|WHILEBLOCK|TASK_CALL)
ROUTINE_STATEMENTS = (ASSIGNMENT|FORBLOCK|CASEBLOCK|IFBLOCK|ASSERTION|REPORT|DELAY_STMT|WHILEBLOCK|TASK_CALL)
PRO_STATEMENTS  = (ASSIGNMENT|FORBLOCK|CASEBLOCK|IFBLOCK|ASSERTION|REPORT)

PROBLOCK = (PRO|APRO|SPRO) CALL_ARG_LIST COLON

ROUTINE_BLOCK = ROUTINE LPAREN (SINGLE|REPEAT) RPAREN COLON

FORBLOCK = FOR ID ASSIGN SIMP_EXPR COLON

WHILEBLOCK = WHILE LPAREN SIMP_EXPR RPAREN COLON

CASEBLOCK = CASE LPAREN SIMP_EXPR RPAREN COLON
CASE_CHOICE = CHOICE COLON
CHOICE = (SLICE|ID|OTHERS)

IFBLOCK   = IF LPAREN SIMP_EXPR RPAREN COLON
ELIFBLOCK = ELIF LPAREN SIMP_EXPR RPAREN COLON
ELSEBLOCK = ELSE COLON

MODULE_INST = ID ID (LPAREN ID RPAREN)? COLON

ASSERTION = ASSERT SIMP_EXPR COLON

REPORT = (PRINT|WARNING|ERROR) CALL_ARG_LIST

RENAME_STMT = RENAME VAR ASSIGN CONST

RETURN_STMT = RETURN (SIMP_EXPR|CALL_ARG_LIST)

DELAY_STMT = (DELAY_TIME | DELAY_COND | DELAY_ON)
DELAY_TIME = DELAY SIMPLE_EXPR
DELAY_COND = DELAY UNTIL SIMP_EXPR
DELAY_ON = DELAY ON SIMP_EXPR

ASSIGNMENT = VAR (ASSIGN|CMPD_ARITH_ASSIGN|CMPD_LOGICAL_ASSIGN) CMPX_EXPR

CMPX_EXPR = AGGREGATE | SIMP_EXPR
AGGREGATE = LBRACK ELEM_ASSOC (COMMA ELEM_ASSOC)* RBRACK
ELEM_ASSOC = CHOICE ASSIGN (AGGREGATE | SIMP_EXPR)

SIMP_EXPR = RELATION (LOGICAL_OPER RELATION)*
RELATION = SHIFT (RELATION_OPER SHIFT)*
SHIFT = TERM (SHIFT_OPER TERM)*
TERM = FACT ((ADD_SUB | CAT) FACT)*
FACT = EXPONENT ((STAR | DIV | MOD_REM) EXPONENT)*
EXPONENT = UNARY (EXP UNARY)*
UNARY = (ADD_SUB | NOT)? PRIMARY
PRIMARY = CONST | REPLICATE | (LPAREN SIMP_EXPR RPAREN) | FUNC_CALL | VAR
FUNC_CALL = ID CALL_ARG_LIST
REPLICATE = LCURBRAC SIMP_EXPR RCURBRAC
CONST = (INTEGER | FLOAT | BIT_INIT | STRING | BOOLEAN)
VAR = ID (INDEX_LIST)? (DOT ID (INDEX_LIST)?)?
INDEX_LIST = (LBRACK SLICE RBRACK)*
SLICE = SIMP_EXPR (COLON SIMP_EXPR)?
```
### Semantic Analysis

The semantic analyzer is a two pass module that first checks simple rules of the
FDL language, then compiles the code based on the top level module with defined 
generics.

Not much work has gone into this.

### Translator

This module will take the FDL abstract syntax tree and translates it to VHDL 
language. 

No work has gone into this.
