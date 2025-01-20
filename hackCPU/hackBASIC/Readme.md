hack BASIC:

A simple micro Basic implementation in the Jack language for the hack Computer.

EDITING AND LINE FORMATS
     1.  Line numbers must be between 1 and 32762 
     2.  Lines are appended and/or inserted 
     3.  Line number alone followed by C/R deletes the line 
     4.  Blanks are immaterial, except key words must contain no embedded blanks 
     5.  The system prompts with a "#" 
     6.  Multiple statement lines are not permitted 

COMMANDS
     1.  NEW     - Deletes all lines and data 
     2.  LIST    - Lists the program      
     3.  RUN     - Executes program consisting of the numbered statements 
     4.  Any line without a line number is executed immediately 
         Example: PRINT (47+56) *15 
     5.  A "Break" will terminate program execution and return to "#" 

INPUT/OUTPUT
     1.  INPUT Statement 
         A.  INPUT X
             System prompts with "?" on an input command 
             Entry of numbers out of the range ± 32762 causes an error 
     2.  PRINT
         A.  PRINT  - Prints a blank line 
         B.  PRINT A,B,C
         C.  PRINT "LITERAL STRING"
         D.  PRINT A; "TIMES"; B; "EQUALS"; A*B
             A semicolon creates a single space between elements 
             whereas a comma is used for zone spacing. (See tab function) 
             A semicolon at the end of the print line suppresses C/R and LF 

VARIABLES 
 
     1.  26 Variable names A,B,C,D ....Z are allowed 
     2.  range +/- 32762 
     3.  No string variables (Strings can only be used in print statements) 
 
EXPRESSIONS 
 
         A.  X 
         B.  X+Y *(5-Z) 
         C.  (X+Y) * (X-Y)/(X * Y) 
         D.  Divide by zero causes error printout 
         E.  Abbreviated below as "EXPR" to show how statements work 
         F.  Double byte integer math only 
         G.  Overflow over/under + 31762 causes error on multiply and divide 
             no error on addition or subtraction overflow. 
 
ASSIGNMENT STATEMENTS 
 
         A.  LET (VARIABLE)=EXPR 
             Examples: 
                 LET X = Y 
                 LET Y = 10+C 
                 LET A(10,X) = (X+Y)*5 - (Z+3)*50  
         B.  Can be implied  
             Example: 
                 Y = A*B + 1976 
 
RELATIONSHIP TEST 
 
         A.  IF EXPR (RELATIONSHIP) EXPR (STATEMENT)  
         B.  RELATIONSHIP can be: 
                  <, >, =, <>, ><, <=, >= 
         C.  Examples: 
                 IF X = Y GOTO 30 
                 IF X+5 = 2*Y-7 LET X=Y 
                 IF A <> B PRINT "WRONG" 
 
CONTROL STATEMENTS 
 
     1.  GOTO (EXPR)  
             Examples: 
                 GOTO 35 
                 GOTO R+50 

     2.  GOSUB (EXPR) 
             Examples: 
                 GOSUB 8000 
                 GOSUB Z*1000 

     3.  RETURN 
         A.  Must be preceded by a GOSUB 
     
     4.  FOR and NEXT 
         A.  FOR (VARIABLE) = (EXPR) TO (EXPR) 
         B.  Examples: 
              FOR J = 1 TO 20  
         C.  Step is 1 only 
         D.  FOR Loops can be nested 
         E.  Branching out of the loops without indexing the variable is not permitted due to stack control problems 

     5.  NEXT Variable: 
         A.  Examples: 
              NEXT J  
         B.  Indexes the FOR variable by one. 
 
FUNCTIONS 
 
     1.  TAB (EXPR) - Starts next print element at position specified by 
    EXPR 
    A.  Examples: 
            PRINT TAB (20); I; TAB (40); "YES" 
            PRINT TAB (X+5); "*"  
    B.  If print element is past point defined, printing starts at present print position 
 
    

ERROR MESSAGES
     1.  ERROR #______________ IN LINE #______________ 
          A.  If LINE # = 00000 error was in direct execution statement 
     2.  Error Codes: 
       1.  Input line over 72 characters 
       2.  Numeric overflow 
       3.  Illegal character or variable 
       4.  No ending " in print literal 
       5.  Dimensioning error 
       6.  Illegal arithmetic 
       7.  Line number not found 
       8.  Divide by zero attempted 
       9.  Excessive subroutine nesting (max is 8) 
      10.  RETURN without prior GOSUB
      11.  Illegal variable 
      12.  Unrecognizable statement 
      13.  Parenthesis error 
      14.  Memory full 
      15.  Subscript error 
      16.  Excessive FOR loops active (Max is 8) 
      17.  NEXT "X" without FOR
 