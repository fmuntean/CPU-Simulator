
Build a simple CPU simulator:


CPU:
 8bit CPU
 memory is shared between program and data
 addressing 256 bytes of memory
 2 8bit general registers 
	REG A
	REG B
 One Register for flags (SR):
	ZERO, when REG A is set to zero by load or any operation 
	CARRY when the value in the REG A is overflowing
 One PC register or program counter that starts at zero when reset
 
 Minimum set of CPU instructions: 
| OPERATION | DESCRIPTION |
| ------------- | ------------- |
| NOP |			No operation |
| HALT |		Stops execution and return to debugger |
| LC A/B, constant |	Loads a constant directly in register A or B |
| LD A/B, memory |	Loads a value in register A or B from memory location |
| ST A/B, memory |	Store A or B register value into the memory location |
| STOAB	|		Store the value in register B into the memory location referenced into register a |
| ADD 	|		Store the sum of both the registers into register A (A+B => A)<br>- if result greater than 255 then CARRY is set<br>- if result % 256 is zero then ZERO is set |
| SUB | 		Subtract the register B from A and store the result into register A (A-B => A)<br>- if result less than zero then CARRY is set<br>- if result equal to zero then ZERO is SET |
| JMP memory |		Unconditional jump to specific memory address location |
| JMPZ memory |		Jump if ZERO is set to specific location; otherwise continue |
| JMPC memory |		Jump if CARRY is set to specific location; otherwise continue |

Extra set of optional instructions:
| OPERATION | DESCRIPTION |
| ------------- | ------------- |
| AND |	Bitwise AND between registers A and B and store result in register A |
| OR | 					Bitwise OR between registers A and B and store result in register A |
| XOR | 				Bitwise XOR between registers A and B and store result in register A |
| LSR | 				Logical shift right<br>- if result is zero then ZERO flag is set<br>- if least significant bit is 1 then CARRY is set |
| LSL | 				Logical shift left<br>- if most significant bit is 1 then CARRY is set<br>- if result is zero then ZERO flag is set |

># Note:
		For AND,OR,XOR operations if result is 0 then the ZERO flag is set
		Operations where flags are not mentioned to be affected are leaving the flags alone 
		and not clearing them thus allowing for delayed check and optimizations |

 Simulator:
	Should allow for visualization of internal CPU registers and flags 
	Should allow for memory visualization
	
 Simulator commands:
	quit/exit 			to exit program
	run 				run program from current PC and stop on HALT instruction
	reset 				to reset PC, registers and flags to zero allow for optional PC value to be set
	regs 				to display internals registers, PC , FLAGS in hex or binary format
	set memory,value 	to write a value to specific memory location
	
	save filename 		to save the entire memory to file
	load filename 		to load the entire memory to file
	step 				to single step the program one instruction at the time
	
	hex					allow for setting multiple hex values

Note:
The simulator should include a way to load both raw binary memory and hex formatted files
The HEX file format is as text file where each line starts with the address then ':' followed by a list of hex values separated by space
the load command can differentiate between the hex and binary files by extension

Compiler:
	simple compiler to generate hex codes from asm text files
	if a line starts with :label that location will be marked and can be used for jump operations
	.ORG to allow the code to start at specific memory location
	.DATA to allow for just adding hex values separated by space at current location
	; is used for comments


	
	
pip install windows-curses
	
 
