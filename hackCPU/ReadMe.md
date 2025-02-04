Hack CPU and computer simulation:

https://en.wikipedia.org/wiki/Hack_computer
https://nand2tetris.github.io/web-ide
https://www.nand2tetris.org
https://www.coursera.org/learn/nand2tetris1
https://www.coursera.org/learn/nand2tetris2
https://github.com/BradenCradock/nand2tetris/tree/master

Syntax file is vendored from: https://github.com/Throvn/vscode-nand2tetris

Snippets from: https://github.com/AvivYaish/nand-ide


VSCode extension: https://github.com/amadeann/nand2tetris-jack-syntax-vscode




Hack CPU:
    Two registers: A and D
    M == RAM[A]

Hack Assembly Instructions:
    A instruction:
        @value  between 0 and 32767 (15bits)
    
    C instruction:
        dest = comp ; jump (dest and jump are optional)

Hack machine language computation function codes and assembly language mnemonics

|a|c1|c2|c3|c4|c5|c6|                   ALU Output: f(x,y)                          | Mnemonic |
|-|--|--|--|--|--|--|---------------------------------------------------------------|---|
|0| 1| 0| 1| 0| 1| 0| Outputs 0;                              ignores all operands  |0  |
|0| 1| 1| 1| 1| 1| 1| Outputs 1;                              ignores all operands  |1  |
|0| 1| 1| 1| 0| 1| 0| Outputs -1;                             ignores all operands  |-1 |
|0| 0| 0| 1| 1| 0| 0| Outputs D;                              ignores A and M       |D  |
|0| 1| 1| 0| 0| 0| 0| Outputs A;                              ignores D and M       |A  |
|1| 1| 1| 0| 0| 0| 0| Outputs M;                              ignores D and A       |M  |
|0|	0| 0| 1| 1| 0| 1| Outputs bitwise negation of D;          ignores A and M       |!D |
|0|	1| 1| 0| 0| 0| 1| Outputs bitwise negation of A;          ignores D and M       |!A |
|1|	1| 1| 0| 0| 0| 1| Outputs bitwise negation of M;          ignores D and A       |!M |
|0|	0| 0| 1| 1| 1| 1| Outputs 2's complement negative of D;   ignores A and M       |-D |
|0|	1| 1| 0| 0| 1| 1| Outputs 2's complement negative of A;   ignores D and M       |-A |
|1|	1| 1| 0| 0| 1| 1| Outputs 2's complement negative of M;   ignores D and A       |-M |
|0|	0| 1| 1| 1| 1| 1| Outputs D + 1 (increments D);           ignores A and M       |D+1|
|0|	1| 1| 0| 1| 1| 1| Outputs A + 1 (increments A);           ignores D and M       |A+1|
|1|	1| 1| 0| 1| 1| 1| Outputs M + 1 (increments M);           ignores D and A       |M+1|
|0|	0| 0| 1| 1| 1| 0| Outputs D - 1 (decrements D);           ignores A and M       |D-1|
|0|	1| 1| 0| 0| 1| 0| Outputs A - 1 (decrements A);           ignores D and M       |A-1|
|1|	1| 1| 0| 0| 1| 0| Returns M-1 (decrements M);             ignores D and A       |M-1|
|0|	0| 0| 0| 0| 1| 0| Outputs D + A;                          ignores M	            |D+A|
|1|	0| 0| 0| 0| 1| 0| Outputs D + M;                          ignores A	            |D+M|
|0|	0| 1| 0| 0| 1| 1| Outputs D - A;                          ignores M	            |D-A|
|1|	0| 1| 0| 0| 1| 1| Outputs D - M;                          ignores A	            |D-M|
|0|	0| 0| 0| 1| 1| 1| Outputs A - D;                          ignores M	            |A-D|
|1|	0| 0| 0| 1| 1| 1| Outputs M - D;                          ignores A	            |M-D|
|0|	0| 0| 0| 0| 0| 0| Outputs bitwise logical And of D and A; ignores M	            |D&A|
|1|	0| 0| 0| 0| 0| 0| Outputs bitwise logical And of D and M; ignores A	            |D&M|
|0|	0| 1| 0| 1| 0| 1| Outputs bitwise logical Or of D and A;  ignores M	            |D|A|
|1|	0| 1| 0| 1| 0| 1| Outputs bitwise logical Or of D and M;  ignores A	            |D|M|

 Hack machine language computation result storage codes and assembly language mnemonics

|d1|d2|d3|	Store ALU output in	|Mnemonic|
|--|--|--|----------------------|:---|
|0 |0 |0 |	Output not stored   |none|
|0 |0 |1 |	M	                |   M|
|0 |1 |0 |	D	                |   D|
|0 |1 |1 |	M and D	            |  MD|
|1 |0 |0 |	A	                |   A|
|1 |0 |1 |	A and M	            |  AM|
|1 |1 |0 |	A and D	            |  AD|
|1 |1 |1 |	A and M and D	    | AMD|

Hack machine language branch condition codes and assembly language mnemonics

|j1 |j2 |j3 | 	    Branch if               |Mnemonic|
|---|---|---|-------------------------------|----|
|0	|0	|0	|No branch                      |none|
|0	|0	|1	|Output greater than 0	        | JGT|
|0	|1	|0	|Output equals 0                | JEQ|
|0	|1	|1	|Output greater than or equal 0	| JGE|
|1	|0	|0	|Output less than 0	            | JLT|
|1	|0	|1	|Output not equal 0             | JNE|
|1	|1	|0	|Output less than or equal 0    | JLE|
|1	|1	|1	|Unconditional branch	        | JMP|






VM Commands:
    Memory Access:
        push segment i
        pop segment i
        
    Arithmetic/Logical:
        add
        sub
        neg
        eq
        gt
        lt
        and
        or
        not
    
    Branching:
        label label
        goto label
        if-goto label
    
    Functions:
        function functionName nVars
        call functionName nArgs
        return


VM programming convention:
    One file in any VM program is expected to be named Main.vm;
    One VM function in this file is expected to be named main

VM implementation convention:
    When the VM implementation start running or reset it starts executing 
    the argument-less OS function Sys.init
    Sys.ini calls Main.main then enters an infinite loop

ROM address 0:
    SP=256
    Call Sys.ini


Hack Computer RAM (32Kx16bits):
    0 --    15 = Pointers and registers
   16 --   255 = Static Variables
  256 --  2047 = Stack
 2048 -- 16383 = heap
16384 -- 24576 = Memory Mapped IO (Screen + Keyboard)
24577 -- 32767 = Unused memory

Hack Computer ROM (32Kx16bits):
  - program space only

