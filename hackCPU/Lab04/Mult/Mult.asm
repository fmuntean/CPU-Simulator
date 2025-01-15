// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
// The algorithm is based on repetitive addition.

//// Replace this comment with your code.

// this program computes the value R0*R1 and stores the result in R2.

//set R2 to zero
@R2
M=0

(loop)
//loop for R1
@R1
D=M //load R1

@R2
M=D+M //add R1

@R0
MD=M-1 //decrement R0

@loop
D;JGT


