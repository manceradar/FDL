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

TODO

## Syntax Parsing

FILE = (IMPORT_STMT|LIB_DECL|MODULE_DECL|TESTBENCH_DECL)

IMPORT_STMT = IMPORT ID (DOT ID)?

LIB_DECL = LIBRARY ID COLON
LIB_BLOCK = (FUNC_DECL|TASK_DECL|STRUCT_DECL|INTERFACE_DECL|VAR_DECL|ENUM_DECL)

STRUCT_DECL = STRUCT ID (DECL_ARG_LIST)? COLON
STRUCT_FIELD = TYPE (CALL_ARG_LIST)? (INDEX_LIST)? ID

INTERFACE_DECL = INTERFACE ID (DECL_ARG_LIST)? COLON
INTERFACE_FIELD = TYPE (CALL_ARG_LIST)? (INDEX_LIST)? BASE_INTERFACE ID

FUNC_DECL = FUNCTION (ID|*_OPER) DECL_ARG_LIST COLON

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
TESTBENCH_LOGIC = (ASSIGNMENT|FORBLOCK|CASEBLOCK|IFBLOCK|ASSERTION|PROBLOCK|MODULE_INST|SEQBLOCK|TASK_CALL)

ARCH_STATEMENTS = (ASSIGNMENT|FORBLOCK|CASEBLOCK|IFBLOCK|ASSERTION|PROBLOCK|MODULE_INST|RENAME_STMT)
FUNC_STATEMENTS = (ASSIGNMENT|FORBLOCK|CASEBLOCK|IFBLOCK|ASSERTION|REPORT|RETURN_STMT)
TASK_STATEMENTS = (ASSIGNMENT|FORBLOCK|CASEBLOCK|IFBLOCK|ASSERTION|REPORT|WAIT_STMT|WHILEBLOCK|TASK_CALL)
SEQ_STATEMENTS = (ASSIGNMENT|FORBLOCK|CASEBLOCK|IFBLOCK|ASSERTION|REPORT|WAIT_STMT|WHILEBLOCK|TASK_CALL)
PRO_STATEMENTS  = (ASSIGNMENT|FORBLOCK|CASEBLOCK|IFBLOCK|ASSERTION|REPORT)

PROBLOCK = (PRO|APRO|SPRO) CALL_ARG_LIST COLON

SEQBLOCK = SEQ (CALL_ARG_LIST)? COLON

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

WAIT_STMT = (WAIT_TIME WAIT_COND WAIT_)

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


