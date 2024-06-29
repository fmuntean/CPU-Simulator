; Adds two numbers stored at specific addresses: F0 and F1
; Stores the result in FE (MSB) and FF (LSB)

; assemby for myCPU

.ORG BF
:end
HALT

.ORG 0
LD A,F0
LD B,F1
ADD
ST A,FF
JMPC :set1
JMP :end

:set1
LC A,1
ST A,FE
JMP BF



.ORG F0
.DATA 01 03


