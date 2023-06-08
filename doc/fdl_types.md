# Types
# All types are subtypes of 'bit'
```
bit - values ['0','1','Z','X','L','H','-']
bool - values [True, False]
uint(integer numBits) - values [integer]
sint(integer numBits) - values [integer]
ufix(uint wholeBits, uint fixedBits) - values [integer,float]
sfix(uint wholeBits, uint fixedBits) - values [integer,float]
float - values [float]
str - values [string]
enum - values [string]
```

# Subtypes
struct - collection of types
interface - collection of types with configurable ports

# Port Types
in
out
inout
producer
consumer

# Type Attributes
dim()                    # Returns integer of number of dimensions
left(uint dim=0)         # Returns integer of left index of dimension 'dim'
right(uint dim=0)        # Returns integer of right index of dimension 'dim'
range(uint dim=0)        # Returns list of integers over dimension 'dim'
length(uint dim=0)       # Returns integer of length of dimension 'dim'
ascending(uint dim=0)    # Returns integer of length of dimension 'dim'
typeStr()                # Returns string of data type name

# Struct Attributes
toBits()                 # Returns bit vector serialized.
fromBits(bit* x)         # Deserialize bit vector and assigns to itself

# Built-in VHDL Functions
bit not(bit arg)
bit and(bit left, bit right)
bit or(bit left, bit right)
bit xor(bit left, bit right)
bit nand(bit left, bit right)
bit nor(bit left, bit right)
bit xnor(bit left, bit right)
bit* not(bit* arg)
bit* and(bit* left, bit* right)
bit* or(bit* left, bit* right)
bit* xor(bit* left, bit* right)
bit* nand(bit* left, bit* right)
bit* nor(bit* left, bit* right)
bit* xnor(bit* left, bit* right)

sint abs(sint arg)

uint add(uint left, uint right)
sint add(sint left, sint right)
uint sub(uint left, uint right)
sint sub(sint left, sint right)
uint mult(uint left, uint right)
sint mult(sint left, sint right)
uint div(uint left, uint right)
sint div(sint left, sint right)
uint mod(uint left, uint right)
sint mod(sint left, sint right)
uint rem(uint left, uint right)
sint rem(sint left, sint right)

bool lt(uint left, uint right)
bool lt(sint left, sint right)
bool gt(uint left, uint right)
bool gt(sint left, sint right)
bool lteq(uint left, uint right)
bool lteq(sint left, sint right)
bool gteq(uint left, uint right)
bool gteq(sint left, sint right)
bool eq(uint left, uint right)
bool eq(sint left, sint right)
bool ne(uint left, uint right)
bool ne(sint left, sint right)

uint sll(uint left, uint right)
sint srl(sint left, sint right)
uint sla(uint left, uint right)
sint sra(sint left, sint right)
uint sll(uint left, uint right)
sint sll(sint left, sint right)
uint rol(uint left, uint right)
uint rol(uint left, sint right)
sint rol(sint left, uint right)
sint rol(sint left, sint right)
uint ror(uint left, uint right)
uint ror(uint left, sint right)
sint ror(sint left, uint right)
sint ror(sint left, sint right)

uint resize(uint arg, uint size)
sint resize(sint arg, uint size)

uint not(uint arg)
uint and(uint left, uint right)
uint or(uint left, uint right)
uint xor(uint left, uint right)
uint nand(uint left, uint right)
uint nor(uint left, uint right)
uint xnor(uint left, uint right)
sint not(sint arg)
sint and(sint left, sint right)
sint or(sint left, sint right)
sint xor(sint left, sint right)
sint nand(sint left, sint right)
sint nor(sint left, sint right)
sint xnor(sint left, sint right)

float sign(float arg)
float ceil(float arg)
float floor(float arg)
float round(float arg)
float trunc(float arg)
float max(float left, float right)
float min(float left, float right)
float sqrt(float arg)
float cbrt(float arg)
float pow(uint left, float right)
float pow(float left, float right)
float exp(float arg)
float log(float arg)
float log(uint base, float arg)

# Built-in FDL Functions
sint  ceil(float arg)
sint  floor(float arg)
sint  round(float arg)
sint  trunc(float arg)
float log2(float arg)
float log2c(float arg)
sint  log2c(float arg)
sint  log2c(sint arg)
uint  log2c(float arg)
uint  log2c(uint arg)
float log10(float arg)

# Types

bit  bit(bool arg)
bit* bit(uint arg)
bit* bit(sint arg)
bool bool(bit arg)
uint uint(bit* arg)
uint uint(sint arg)
uint uint(float arg)
sint sint(bit* arg)
sint sint(uint arg)
sint sint(float arg)


# Direct 
rising
falling
pro
spro
apro

