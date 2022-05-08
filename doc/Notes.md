# Overall Language Construct

This document covers how the FPGA Description Language (FDL, pronounced "Fiddle")
language construction and how the compiler works.

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
| bit       | 0,1,Z,X,L,H,- | `bit foo = '1'` |
| bool | True, False | `bool bar = False` |
| uint(sint numBits = 32) | integer | `uint(8) foo = 100` |
| sint(sint numBits = 32) | integer | `sint bar = -100` |
| ufix(sint wholeBits, sint fixedBits) | integer, float | `ufix(8,8) foo = 8.0625` |
| sfix(sint wholeBits, sint fixedBits) | integer, float | `sfix(0,15) bar = -0.25` |
| float | float | `float foo = 3.14` |
| str | string | `str bar = "Data ready!\n"` |
| enum | string | `enum baz = {stReady, stRead, stWrite, stWait}` |
| time | float, integer | `time foo = 4 ns` |
| freq | float, integer | `freq bar = 100 MHz` |

Unlike VHDL, FDL data types are classes. The base data types contain functions that
define all the base operations, including FDL extended functions. 

FDL also extends the language for allow for data consolidation using records/structs
and interfaces. Most of the tools don't support these features, but FDL expands the
variables behind the scenes such that the tools are happy. Additionally, these types
considered as classes. 

The structure data type allows for data consolidation when all the ports are going
in one direction. Additionally, functions can be defined to extend functionality.

```
struct complex(uint numBits):
  sint(numBits) real
  sint(numBits) imag
  bit           valid
  bit           lock
    
impl complex:
  function is_ready() -> bit:
    return (valid and not(lock))
```

The interface data type is very similar to the structure data type, but allows the 
user to define the direction of the underlying data with depending on the driver type;
producer or consumer. Furthermore, interfaces can have processes defined under them to
run code. This makes them similar to modules, but class is passed around as ports and 
their functions follow them. 

```
interface stream<T>:
  T     producer payload
  bit   producer valid
  bit   consumer ready
```

When a port is defined as 'producer', it means the producer drives the signal as
an output. When the entire interface class is defined as a producer, all producer
ports are defined as output and consumer ports are defined as inputs; and vice versa
for consumer interfaces.

### Data Arrays

FDL handles arrays differently than VHDL. Instead of unique data types for each 
array size, arrays are handled like C. FDL allows the user to extend any data type
automatically. Additionally, arrays can be assign using curly braces.

```
# 1 dimensional array
sint(8)[3:0] = [4, 5, 9, 2]
# 2 dimensional array
uint[0:3][0:1] = [[1,2], [3,4], [5,6], [7,8]]
```

For function calls, the data array dimension needs to be specified by using the '*' 
character. The dimension size doesn't need to be known, but can be determined in the
function.

```
# and function with two, one dimensional 'bit' inputs
function and(bit* left, bit* right) -> bit*:
```

### Libraries

Similar to packages in VHDL, libraries contain common values, configuration parameters, 
structures, interfaces, 

### Modules

Modules are defined similarly to VHDL. A module is equivalent to an entity in VHDL.
There is an optional generic and required port declaration for modules. Generics
can have default values, but not required. Module instances must have all generic
values defined either through assignment or default values. An example of a module
named 'Delay' with one generic and three ports.

```
module Delay:
  generics:
    sint stages = 4
  ports:
    bit  in  clk
    bit  in  input
    bit  out output
    
arch rtl for Delay:
  declare:
    # Shift register
    bit[stages:1]  reg = [others='0']

  logic:
 
    spro(clk,rst):
      reg  = reg[stages-1:2] & in
      
    output = reg[stages]
```

Notice 'rtl' architecture for the Delay module is first defined. The next
section defines the internal signal definition with the 'declare' statement. Next,
the 'logic' section defines the actual logic to be performed the the module.

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

| FDL Keywords |FDL Keywords|FDL Keywords|FDL Keywords|
|---|---|---|---|
| import | library | func | enum |
| module | blackbox | generics | ports |
| in | out | inout | producer |
| consumer | arch | declare | logic |
| **rename** | for | case | struct |
| interface | const | others | pro |
| spro | apro | if | elif |
| else | return | assert | print |
| warning | error | delay | until |
| on | task | single | repeat |
| while | routine | open | not |
| attr | next | exit | type |
| and | or | nand | nor |
| xor | xnor | sll | srl |
| sla | sra | ror | rol |
| mod | rem | trait | impl |
| self | as | Self | |

### Syntax Parsing

Syntax parsing rules follow regular expression rules

* '*' means to match zero or more occurances
* '(FOO | BAR)' means to match FOO or BAR
* '?' means to match zero or one occurance
* '+' means to match one or more occurances

```

COMMENT = HASH (.)*
COMMENT_HEADER = HASH BANG (.)*
COMMENT_FMT = HASH HASH (.)*


ITEM = (LIB_DECL|
        MODULE_DECL|
        TESTBENCH_DECL|
        IMPORT_STMT|
        STRUCT_DECL|
        INTERFACE_DECL|
        TRAIT_DECL|
        INHERENT_IMPL|
        TRAIT_IMPL|
        FUNC_DECL|
        TASK_DECL|
        CONST_VAR_DECL|
        ATTR_DECL|
        ENUM_DECL)

IMPORT_STMT = IMPORT ID (DOT ID)* (AS ID)?

LIB_DECL = LIBRARY ID COLON (BASE_DECL_STMT)*
BASE_DECL_STMT = (STRUCT_DECL|
                  INTERFACE_DECL|
                  TRAIT_DECL|
                  INHERENT_IMPL|
                  TRAIT_IMPL|
                  FUNC_DECL|
                  TASK_DECL|
                  SIGNAL_VAR_DECL|
                  ATTR_DECL|
                  ENUM_DECL)

STRUCT_DECL = STRUCT ID (GENERIC_PARAMS)? (DECL_ARG_LIST)? COLON
STRUCT_FIELD = VAR_DECL

INTERFACE_DECL = INTERFACE ID (GENERIC_PARAMS)? (DECL_ARG_LIST)? COLON
INTERFACE_FIELD = TYPE_DECL EXT_INTERFACE ID

TRAIT_DECL = TRAIT ID (GENERIC_PARAMS)? COLON
TRAIT_ITEM = (CONST_VAR_DECL |
              ATTR_DECL |
              FUNC_DEF | 
              FUNC_DECL | 
              TASK_DEF | 
              TASK_DECL)

TRAIT_NAME = ID (DOT ID)*
STR_INT_NAME = ID (DOT ID)*
INHERENT_IMPL = IMPL (GENERIC_PARAMS)? STR_INT_NAME (GENERIC_PARAMS)? COLON
TRAIT_IMPL = IMPL (GENERIC_PARAMS)? TRAIT_NAME (GENERIC_PARAMS)? FOR STR_INT_NAME (GENERIC_PARAMS)? COLON
IMPL_ITEM = (CONST_VAR_DECL |
             ATTR_DECL |
             FUNC_DECL |
             TASK_DECL)

DECLARE_DECL = DECLARE COLON
LOGIC_DECL = LOGIC COLON

FUNC_DEF = FUNC FUNC_NAME (GENERIC_PARAMS)? (DECL_ARG_LIST)? RARROW RETURN_TYPE
FUNC_DECL = FUNC_DEF COLON
FUNC_NAME = (ID | LOGICAL_OPER | SHIFT_OPER | MOD_REM_OPER | NOT_OPER)
FUNC_STMT = (DECLARE_DECL BASE_DECL_STMT)? LOGIC_DECLARE FUNC_LOGIC_STMT
RETURN_TYPE = (LPAREN TYPE_NAME (COMMA TYPE_NAME)* RPAREN) | TYPE_NAME

FUNC_LOGIC_STMT = (ASSIGNMENT|
                   METHOD_TASK_CALL|
                   FORBLOCK|
                   CASEBLOCK|
                   IFBLOCK|
                   ASSERTION|
                   REPORT|
                   RETURN_STMT)

TASK_DEF = TASK TASK_NAME (GENERIC_PARAMS)? (DECL_ARG_LIST)? RARROW RETURN_TYPE
TASK_DECL = TASK_DEF COLON
TASK_NAME = ID
TASK_STMT = (DECLARE_DECL BASE_DECL_STMT)? LOGIC_DECLARE TASK_LOGIC_STMT
TASK_LOGIC_STMT = (ASSIGNMENT|
                   METHOD_TASK_CALL|
                   FORBLOCK|
                   CASEBLOCK|
                   IFBLOCK|
                   ASSERTION|
                   PROBLOCK|
                   MODULE_INST|
                   RETURN_STMT)

GENERIC_PARAMS = LT GENERIC_TYPE (COMMA GENERIC_TYPE)* GT
GENERIC_TYPE = ID (DOT ID)*

DECL_ARG_LIST = LPAREN (DECL_ARG)? (COMMA DECL_ARG)* RPAREN
DECL_ARG = TYPE_ARG ID
TYPE_ARG = TYPE_NAME (GENERIC_PARAMS)? (STAR)*

TYPE_DECL = TYPE_NAME (GENERIC_PARAMS)? (CALL_ARG_LIST)? (INDEX_LIST)?

TYPE_NAME = ID (DOT ID)*

CALL_ARG_LIST = LPAREN (SIMP_EXPR)? (COMMA SIMP_EXPR)* RPAREN

VAR_DECL = TYPE_DECL ID
CONST_VAR_DECL = CONST VAR_DECL ASSIGN CMPX_EXPR

ENUM_DECL = ENUM ID ASSIGN LPAREN ID (COMMA ID)* RPAREN

ATTR_DECL = ATTR LPAREN ATTR_SPEC (COMMA ATTR_SPEC)* RPAREN FOR TYPE_NAME
ATTR_SPEC = ID ASSIGN SIMP_EXPR

MODULE_DECL = MODULE ID (GENERIC_PARAMS)? (LPAREN BLACKBOX RPAREN)? COLON
MODULE_STATEMENTS = (MODULE_GENERIC)? MODULE_PORTS

MODULE_GENERIC = GENERICS COLON
GEN_DECL = VAR_DECL (ASSIGN CMPX_EXPR)?

MODULE_PORTS = PORTS COLON
PORT_DECL = TYPE_DECL (BASE_INTERFACE|EXT_INTERFACE) ID

ARCH_DECL = ARCH ID (GENERIC_PARAMS)? FOR ID (GENERIC_PARAMS)? COLON
ARCH_STATEMENTS = (DECLARE_DECL BASE_DECL_STMT)? ARCH_LOGIC ARCH_LOGIC_STMTS
ARCH_LOGIC_STMTS = (ASSIGNMENT|
                    METHOD_TASK_CALL|
                    FORBLOCK|
                    CASEBLOCK|
                    IFBLOCK|
                    ASSERTION|
                    PROBLOCK|
                    MODULE_INST|
                    RENAME_STMT)

PROBLOCK = (PRO|APRO|SPRO) CALL_ARG_LIST COLON
PRO_STATEMENTS  = (ASSIGNMENT|
                   METHOD_TASK_CALL|
                   FORBLOCK|
                   CASEBLOCK|
                   IFBLOCK|
                   ASSERTION|
                   REPORT)

FORBLOCK = FOR ID ASSIGN SIMP_EXPR COLON

WHILEBLOCK = WHILE LPAREN SIMP_EXPR RPAREN COLON

CASEBLOCK = CASE LPAREN SIMP_EXPR RPAREN COLON
CASE_CHOICE = CHOICES COLON

IFBLOCK   = IF LPAREN SIMP_EXPR RPAREN COLON
ELIFBLOCK = ELIF LPAREN SIMP_EXPR RPAREN COLON
ELSEBLOCK = ELSE COLON

MODULE_INST = ID ID (DOT ID)* (GENERIC_PARAMS)? (LPAREN (ID | BLACKBOX) RPAREN)? COLON

ASSERTION = ASSERT SIMP_EXPR COLON

REPORT = (PRINT|WARNING|ERROR) CALL_ARG_LIST

TUPLE_EXPR = LPAREN (SIMP_EXPR)? (COMMA SIMP_EXPR)* RPAREN

RETURN_STMT = RETURN (CPLX_EXPR|TUPLE_EXPR)

ASSIGN_OPTIONS = (ASSIGN|CMPD_ARITH_ASSIGN|CMPD_LOGICAL_ASSIGN)
ASSIGNMENT = (VAR | TUPLE_EXPR) ASSIGN_OPTIONS CMPX_EXPR
FUNC_METHOD_CALL = ID (INDEX_LIST)? (DOT ID (INDEX_LIST)?)* (DOT FUNC_CALL)

CMPX_EXPR = AGGREGATE | SIMP_EXPR
AGGREGATE = LBRACK ELEM_ASSOC (COMMA ELEM_ASSOC)* RBRACK
ELEM_ASSOC = (CHOICES ASSIGN)? (AGGREGATE | SIMP_EXPR)
CHOICES = CHOICE (OR_BAR CHOICE)*
CHOICE = (SLICE | OTHERS)

SIMP_EXPR = RELATION (LOGICAL_OPER RELATION)*
RELATION = SHIFT ((RELATION_OPER|GT|LT) SHIFT)*
SHIFT = TERM (SHIFT_OPER TERM)*
TERM = FACT ((ADD_SUB | CAT) FACT)*
FACT = EXPONENT ((STAR | DIV | MOD_REM) EXPONENT)*
EXPONENT = UNARY (EXP UNARY)*
UNARY = (ADD_SUB | NOT)? PRIMARY
PRIMARY = CONST_VAR | (LPAREN SIMP_EXPR RPAREN) | FUNC_CALL | VAR
FUNC_CALL = FUNC_NAME GENERIC_PARAMS? CALL_ARG_LIST
CONST_VAR = (INTEGER | FLOAT | BIT_INIT | STRING | BOOLEAN)
VAR = (ID | SELF) (INDEX_LIST)? (DOT ID (INDEX_LIST)?)*
VAR_FUNC = (ID | SELF) (INDEX_LIST)? (DOT ID (INDEX_LIST)?)* (DOT FUNC_CALL)
INDEX_LIST = (LBRACK SLICE RBRACK)*
SLICE = SIMP_EXPR (COLON SIMP_EXPR)?







# Testbench features on hold
TESTBENCH_DECL = TESTBENCH ID COLON
TESTBENCH_GENERIC = (GENERICS COLON)?
TESTBENCH_DECLARE = (FUNC_DECL|TASK_DECL|STRUCT_DECL|INTERFACE_DECL|VAR_DECL|ENUM_DECL)
TESTBENCH_LOGIC = (ASSIGNMENT|FORBLOCK|CASEBLOCK|IFBLOCK|ASSERTION|PROBLOCK|MODULE_INST|ROUTINE_BLOCK|TASK_CALL)

ROUTINE_BLOCK = ROUTINE LPAREN (SINGLE|REPEAT) RPAREN COLON
ROUTINE_STATEMENTS = (ASSIGNMENT|FORBLOCK|CASEBLOCK|IFBLOCK|ASSERTION|REPORT|DELAY_STMT|WHILEBLOCK|TASK_CALL)

DELAY_STMT = (DELAY_TIME | DELAY_COND | DELAY_ON)
DELAY_TIME = DELAY SIMPLE_EXPR
DELAY_COND = DELAY UNTIL SIMP_EXPR
DELAY_ON = DELAY ON SIMP_EXPR
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
