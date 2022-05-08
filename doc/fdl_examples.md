# FPGA Description Language Syntax

# Processing Logic

## Synchronous Processes

spro does synchronous process  
Clock edge is rising by default  
Reset level is high ('1') by default  
```
 spro(bit clk):
 spro(bit clk, bit rst):
 spro(bit clk, bit rst, str clkEdge = "rising", str rstLvl = "high):
```

###FDL

```
spro(clk):
  b = a
```

###VHDL

```vhdl
process(clk)
begin
  if rising_edge(clk) then
    b <= a;
  end if;
end process;
```

###FDL
```
bit b = '0'
spro(clk,rst):
  b = a
```

###VHDL
```vhdl
process(clk)
begin
  if rising_edge(clk) then
    if (rst='1') then
      b <= '0';
    else
      b <= a;
    end if;
  end if;
end process;
```

###FDL
```
bit b = '0' 
spro(clk,rst,"falling","low"):
  b = a
```  

###VHDL
```vhdl
process(clk)
begin
  if falling_edge(clk) then
    if (rst='0') then
      b <= '0';
    else
      b <= a;
    end if;
  end if;
end process;
```

## Asynchronous Process
apro does asynchronous process    
Clock edge is rising by default    
Reset level is high ('1') by default      
```
apro(bit clk, bit rst):
apro(bit clk, bit rst, str clkEdge = "rising", str rstLvl = "high):
```

###FDL
```
bit b = '0'
apro(clk,rst):
  b = a
```

###VHDL
```vhdl
process(clk)
begin
  if (rst='1') then
    b <= '0';
  elsif rising_edge(clk) then
    b <= a;
  end if;
end process;
```

###FDL
```
bit b = '0' 
apro(clk,rst,"falling","low"):
  b = a
```

###VHDL
```vhdl
process(clk)
begin
  if (rst='0') then
    b <= '0';
  elsif falling_edge(clk) then
    b <= a;
  end if;
end process;
```


## Traditional process 
pro is a traditional process

###FDL
```
bit b = '0' 
pro:
  if (rst='0'):
    b = '0'
  elif rising_edge(clk):
    b = a
```

###VHDL
```vhdl
process(clk)
begin
  if (rst='0') then
    b <= '0';
  elsif rising_edge(clk) then
    b <= a;
  end if;
end process;
```

# Sequential Logic

## sequential when,else in vhdl

notice its just a normal if,elif,else statement  
this is sequential logic (not in process)  

###FDL
```
if (a=='1'):
  z = '0'
elif (b=='0'):
  z = '1'
else:
  z = 'Z'
```
###VHDL
```vhdl
z <= '0' when a = '1' else
     '1' when b = '0' else
     'Z';
```


## if generate in vhdl
notice its just a normal if,elif,else statement

###FDL
```
if (a=='1'):
  DelayInst Delay(behaviour):
    ports:
      CLK = CLK
      A   = sig1
      B   = sig2
else:
  DelayInst Delay(behaviour):
    ports:
      CLK = CLK
      A   = sig1
      B   = sig3
```

###VHDL
```vhdl
ifgenlabel0 : if (a='1') generate
  DelayInst : Delay(behaviour)
    port map(
      CLK => CLK,
      A   => sig1,
      B   => sig2
    );
else
  DelayInst : Delay(behaviour)
    port map(
      CLK => CLK,
      A   => sig1,
      B   => sig3
    );
end generate;
```


## if,elsif,else in vhdl

###FDL
```
spro(clk):
  if (a=='1):
    z = '0'
  elif (b=='0'):
    z = '1'
  else:
    z = 'Z'
```  

###VHDL
```vhdl
process(clk)
begin
  if rising_edge(clk) then
    if (a='1') then
      z <= '0';
    elsif (b='0') then
      z <= '1';
    else
      z <= 'Z';
    end if;
  end if;
end process;
```

## sequential case in vhdl
notice its just a normal case statement  
this is sequential logic (not in process)  

###FDL
```
case(a):
  '00': b = 1
  '01': b = 2
  '11': b = 3
  '10': b = 4
  else: b = 0
```  

###VHDL
```vhdl
b <= 1 when a = '00' else
     2 when a = '01' else
     3 when a = '11' else
     4 when a = '10' else
     0;
```

## case in vhdl
notice its just a normal case statement

###FDL
```
spro(clk):
  case(a):
    '00': b = 1
    '01': b = 2
    '11': b = 3
    '10': b = 4
```

###VHDL
```vhdl
process(clk)
begin
  if rising_edge(clk) then
    case a is
      when '00' => b <= 1;
      when '01' => b <= 2;
      when '11' => b <= 3;
      when '10' => b <= 4;
    end case;
  end if;
end process;
```

## state machine in vhdl

###FDL
```
spro(clk):
  case(a):
    '00':
      b = 1
      a = '01'
    '01':
      b = 2
      a = '11'
    '11':
      b = 3
      a = '10'
    '10': 
      b = 4
      a = '00'
```

###VHDL
```vhdl
process(clk)
begin
  if rising_edge(clk) then
    case a is
      when '00' =>
        b <= 1;
        a <= '01';
      when '01' =>
        b <= 2;
        a <= '11';
      when '11' =>
        b <= 3;
        a <= '10';
      when '10' =>
        b <= 4;
        a <= '00';
     end case;
  end if;
end process;
```

## for loop in vhdl

###FDL
```
sint(8)[9:0] reg = [others=0]

spro(clk,rst):
  for ind in range(0,9):
    reg[ind] = ind+reg[ind]
```    
###VHDL
```vhdl
signal reg : signed_vec(9 downto 0)(7 downto 0) := (others=>(others=>to_signed(0,8)));

process(clk,rst)
begin
  if rising_edge(clk) then
    if (rst='1') then
      reg <= (others=>(others=>'0'));
    else
      for ind in 0 to 9 loop
        reg(ind) <= to_signed(ind,8) + reg(ind);
      end loop;
    end if;
  end if;
end process;
```

## for generate in vhdl

###FDL
```
for ind in range(0,3):
  DelayInst Delay(behaviour):
    ports:
      CLK = CLK
      A   = sig1(ind)
      B   = sig2(ind)
```  

###VHDL
```vhdl
for ind in 0 to 3 generate
  DelayInst : Delay(behaviour)
    port map(
      CLK => CLK,
      A   => sig1(ind),
      B   => sig2(ind)
    );
end generate;
```

## state machine in vhdl

###FDL
```
enum arb_state = (zero,one,two,three)
arb_state curState = zero
bit[3:0] output = 4{'0'}

spro(clk,rst):
  case (curState):
    zero:   output = '0001'
    one:    output = '0010'
    two:    output = '0100'
    three:  output = '1000'
    else:   output = '0000'
```  
###VHDL
```vhdl
type arb_state is (sm_zero, sm_one, sm_two, sm_three);
signal curState : arb_state := sm_zero;

process(clk,rst)
begin
  if rising_edge(clk) then
    if (rst='1') then
      curState <= sm_zero;
      output   <= (others=>'0');
    else
      case (curState) is
        when sm_zero  => output <= '0001';
        when sm_one   => output <= '0010';
        when sm_two   => output <= '0100';
        when sm_three => output <= '1000';
        when others   => output <= '0000';
      end case;
    end if;
  end if;
end process;
```


# Modules
## module definition in vhdl

###FDL
```
module Delay:
  ports:
    bit in  clk
    bit in  a
    bit out b
    
arch behaviour:
  logic:
    spro(clk):
      b = a
```

###VHDL
```vhdl
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity Delay is
  port(
    CLK : in  std_logic;
    A   : in  std_logic;
    B   : out std_logic
  );
end Delay;

architecture behavior of Delay is

begin
  
  process(CLK)
  begin
    if rising_edge(CLK) then
      B <= A;
    end if;
  end process;
  
end behaviour;
```

## entity definition with generics in vhdl

###FDL
```
module VariableDelay:
  generics:
    sint(8) maxDelay = 8
  ports:
    bit     in  clk
    bit     in  a
    uint(3) in  sel
    bit     out b
    
arch behaviour:
  declare:
    bit[maxDelay-1:0] reg = [maxDelay{'0'}]
  logic:
    spro(clk):
      reg = reg[maxDelay-2:0] & a
      b = reg[sel]
```

###VHDL
```vhdl
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity VariableDelay is
  generic(
    MAXDELAY : signed(7 downto 0) := 8
  );
  port(
    CLK : in  std_logic;
    A   : in  std_logic;
    SEL : in  std_logic_vector(2 downto 0);
    B   : out std_logic
  );
end Delay;

architecture behavior of Delay is
  signal reg : std_logic_vector(MAXDELAY-1 downto 0) :=  '00000000';
begin
  
  process(CLK)
  begin
    if rising_edge(CLK) then
      reg <= reg(MAXDELAY-2 downto 0) & A;
      B   <= reg(to_integer(unsigned(SEL)));
    end if;
  end process;
  
end behavior;
```

## entity instantiation in vhdl

###FDL
```
DelayInst Delay(behaviour):
  ports:
    CLK = CLK
    A   = sig1
    B   = sig2
```
###VHDL
```vhdl
  component Delay is
    port(
      CLK : in  std_logic;
      A   : in  std_logic;
      B   : out std_logic
    );
  end component;

begin

  DelayInst : Delay(behaviour)
    port map(
      CLK => CLK,
      A   => sig1,
      B   => sig2
    );
```

## initialize in vhdl

###FDL
```
const bit zero = '0'
bit[7:0] reg1 = [7:1='0', others='1']
bit[0:7][15:0] reg2 = [others=[others='0']]
```

###VHDL
```vhdl
constant zero : std_logic := '1';
signal reg1 : std_logic_vector(7 downto 0) := (7 downto 1 => '0', others =>  '1');
signal reg2 : std_logic_array(0 to 7)(15 downto 0) := (others=>(others=>'0'));
```

###FDL
```
bit[7:0] reg1 = 8{'0'}
bit[0:7][15:0] reg2 = [others=[others='0']]
```

###VHDL
```vhdl

```


## Structure declaration

###FDL
```
library complexLib:
  struct complex(uint width):
    sint(width) real
    sint(width) imag
    bit         dval
    
module Rotate:
  generic:
    uint(8) w = 8
  ports:
    bit         in  clk
    complex(w)  in  inData
    complex(w)  out outData
    
arch behavior:
  signals:
    complex(w) tmp = [real=0,imag=0,dval='0']
  logic:
    spro(clk):
      tmp.real = inData.real
      tmp.imag = -inData.imag
      tmp.dval = inData.dval
      
    outData = tmp
```
###VHDL
```vhdl
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity Rotate is
  generic(
    W   : signed(7 downto 0) := 8
  );
  port(
    CLK          : in  std_logic;
    INDATA_REAL  : in  signed(w-1 downto 0);
    INDATA_IMAG  : in  signed(w-1 downto 0);
    INDATA_DVAL  : in  std_logic;
    OUTDATA_REAL : out signed(w-1 downto 0);
    OUTDATA_IMAG : out signed(w-1 downto 0);
    OUTDATA_DVAL : out std_logic
  );
end Rotate;

architecture behavior of Rotate is
  signal tmp_real : signed(w-1 downto 0) := to_signed(0,w);
  signal tmp_imag : signed(w-1 downto 0) := to_signed(0,w);
  signal tmp_dval : std_logic := '0';
begin
  
  process(CLK)
  begin
    if rising_edge(CLK) then
      tmp_real <= INDATA_REAL;
      tmp_imag <= -INDATA_IMAG;
      tmp_dval <= INDATA_DVAL;
    end if;
  end process;
  
  OUTDATA_REAL <= tmp_real;
  OUTDATA_IMAG <= tmp_imag;
  OUTDATA_DVAL <= tmp_dval;
  
end behavior;
```

## Function declaration

###FDL
```
library tmpLib:
  # Function to compare 2d bit
  function compare(bit** l, bit** r):
    # Check if array sizes match
    if (l.length(0) != r.length(0)):
      raise error('Dimension does not match')
    
    bool match = True
    for ind=l.range():
      match &= l[ind] == r[ind]
        
    return match
```

###VHDL
```vhdl
package tmpLib is
  type std_logic_2d is array( natural <> ) of std_logic_vector;
  
  -- Function to compare 2d bit
  function compare(l : std_logic_2d, r : std_logic_2d) return boolean;
end tmpLib;

package body tmpLib is
  function compare(l : std_logic_2d, r : std_logic_2d) return boolean is
    variable match : boolean := True;
  begin
    -- Check if array sizes match
    if (l'length /= r'length) then
      assert false
        report "compare: Dimension does not match"
        severity failure;
    end if;
    
    for ind in l'range loop
      match := match and (l(ind) = r(ind));
    end loop;
    
    return match;
  end;
end tmpLib;
```

## Interface declaration

###FDL
```
library busLib:
  # Notice scope in simpleBus
  uint addr_width = 12
  
  # Simple interface definition
  interface simpleBus(uint width):
    bit[width-1:0]       producer data
    bit[addr_width-1:0]  producer addr
    bit                  consumer ready
    bit                  producer valid
    
  interface spi3:
    bit producer sclk
    bit producer sdi
    bit consumer sdo
    bit producer cs_n
    
module SPIMaster:
  generic:
    uint w = 8
  ports:
    bit          in       clk
    simpleBus(w) consumer dataBus
    spi3         producer spiBus
```

###VHDL
```vhdl
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity SPIMaster is
  generic(
    W   : natural := 8
  );
  port(
    CLK           : in  std_logic;
    DATABUS_DATA  : in  std_logic_vector(W-1 downto 0);
    DATABUS_ADDR  : in  std_logic_vector(11 downto 0);
    DATABUS_READY : out std_logic;
    DATABUS_VALID : in  std_logic;
    SPI3_SCLK     : out std_logic;
    SPI3_SDI      : out std_logic;
    SPI3_SDO      : in  std_logic;
    SPI3_CS_N     : out std_logic
  );
end SPIMaster;
```
