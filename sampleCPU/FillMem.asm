; Fill C0 to C8 with incrementing numbers form 1 to 8

; assemby for myCPU

.ORG 00
; initialize memory
LC B,01      
ST B,FF ; store B into FF

LC A,C0
ST A,FE ; store A into FF

:loop
 STOAB 

 LC B,C7
 sub ;A=A-B
 jmpz :end

:inc_B
    LD A,FF
    LC B,01
    ADD
    ST A,FF

:inc_A
    LD A,FE
    LC B,01
    ADD
    ST A,FE

LD B,FF
jmp :loop

:end
 HALT




