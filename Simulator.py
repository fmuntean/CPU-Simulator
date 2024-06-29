from threading import Thread
import time
from ScreenMemory import ScreenMemory
from debugger import Debugger


import curses

cmdPrompt = "> "

"""
:10246200464C5549442050524F46494C4500464C33
|||||||||||                              CC->Checksum
|||||||||DD->Data
|||||||TT->Record Type
|||AAAA->Address
|LL->Record Length
:->Colon
"""
def loadHex(mem,file):
    lines = []
    with open(file,mode="r") as f:
        lines = f.readlines()
    for l in lines:
        if len(l.strip())==0:
            continue
        if l.startswith('//'):
            continue
        if l.startswith(':') & (l[7:9] == '00'):
            count = int(l[1:3],base=16)
            addr = int(l[3:7],base=16)
            for i in range(0,count):
                d = l[9+2*i:9+2*i+2]
                mem[addr]= int(d,base=16)
                addr+=1

# https://en.wikipedia.org/wiki/SREC_(file_format)
# loading motorola s19 files
# currently supporting S1 records
def loadS19(mem,file):
    lines = []
    with open(file,mode="r") as f:
        lines = f.readlines()
    for l in lines:
        if len(l.strip())==0:
            continue
        if l.startswith('//'):
            continue
        if l.startswith('S1'):
            count = int(l[2:4],base=16)
            addr = int(l[4:8],base=16)
            for i in range(0,count-3):
                d = l[8+2*i:8+2*i+2]
                mem[addr]= int(d,base=16)
                addr+=1


def topRefresh(screen,padTop,debugger):
    y, x = screen.getmaxyx()
    padTop.clear()
    topStr = f"{debugger.list_regs()}| |{debugger.get_opcodes()}| {debugger.list_cmd()}"
    padTop.addstr(topStr)
    padTop.refresh(0,0,0,0,0, x-1 )



def main(screen, debugger):
    print(f"Screen Size: {curses.LINES}x{curses.COLS}")
    curses.curs_set(1) # make cursor invisible
    curses.echo(0)
    screen.keypad(1) # interpret arrow keys, etc
    screen.nodelay(True)  # Don't block I/O calls
    screen.timeout(1)
    y, x = screen.getmaxyx()
    #curses.resize_term(0, 0)
    #screen.resize(y,x)
    screen.erase()
    screen.refresh()
    
    padTop = curses.newpad(1,120)
    winBot = curses.newwin(1,x,11,0)
    
    winBot.keypad(1)
    
    winMem = ScreenMemory(screen)
    
                
    while True: # this is the main loop
        screen.erase()
        topRefresh(screen,padTop,debugger)

        winMem.refresh(debugger)
        
        cmdDebug = ''
        while True:
            winBot.erase()
            #winBot.move(0,0)
            winBot.addstr(cmdPrompt)
            winBot.addstr(cmdDebug)
            winBot.addstr(' ',curses.A_BLINK)
            x = len(cmdDebug)+len(cmdPrompt)
            winBot.move(0,x)
            winBot.refresh()
            
            

            try:
                ch =  winBot.getch() #winBot.getkey() #
            except:
                ch = None

            if ch == '\x08' or ch==8 :
                l = len(cmdDebug)-1 if len(cmdDebug)>0 else 0
                cmdDebug=cmdDebug[0:l]
                continue
            if ch == '\t' or ch == 9:
                ret = debugger.execute("step")
                winBot.addstr(ret)
                break
            if ch == "\n" or ch == 10:
                break
            if ch == 451 or ch == 339: # Page Up
                if (debugger.displayStart<0xFF):
                    debugger.displayStart= 0xFFFF+debugger.displayStart-winMem.getBlockSize()
                else:
                    debugger.displayStart-=winMem.getBlockSize() % 0xFFFF
                break
            if ch == 457 or ch == 338: # Page Down
                debugger.displayStart= (debugger.displayStart + winMem.getBlockSize()) % 0xFFFF
                break
            if ch == curses.KEY_RESIZE : # screen resize event
                # Check if screen was re-sized (True or False)
                y, x = screen.getmaxyx()
                #resize = curses.is_term_resized(y, x)
                curses.resize_term(0, 0)
                screen.resize(y,x)
                winMem.resize()
                screen.clear()
                screen.refresh()
                winMem.refresh(debugger)
                
                #winTop.resize(1,x) # curses.newwin(1,x,0,0)
                winBot.resize(1,x) # curses.newwin(1,x,11,0)
                
                topRefresh(screen,padTop,debugger)
                break
            if (ch != None) & (ch < 128) & (ch >=0):
                cmdDebug+=chr(ch)

                
            

        if cmdDebug.lower() == "exit" or cmdDebug.lower() == "quit" or cmdDebug.lower() == 'q':
            break
        
        #screen.refresh()
        ret = executeCommand(debugger,cmdDebug)    

        if ret != None:    
            winBot.addstr("  "+ret)
            winBot.refresh()
        else:    
            time.sleep(1)

        #screen.refresh()
        
def executeCommand(debugger,cmdDebug):
    if len(cmdDebug)==0:
        return None
    
    try:
        ret = debugger.execute(cmdDebug)
    except:
        return 'ERR'
            
    if isinstance(ret,Thread):
        pad = curses.newpad(40,80)
        text = [""]
        
        pad.timeout(1)
        pad.keypad(1)
        #pad.overlay(screen)
        padNeedsRefresh=True
        while ret.is_alive():
            s = ser.transmit()
            if s in (20,19,4):
                s=-1
            if (s>0):
                padNeedsRefresh=True
                if s==13:
                    text.append('')
                else:
                    text[-1]+=chr(s)

            try:
                k = pad.getch()
            except:
                k = None
            if k>0:
                if k==27: # ESC Key
                    b = debugger.breakpoint
                    while ret.is_alive():
                        debugger.breakpoint = debugger.cpu.PC
                        ret.join(1)
                    debugger.breakpoint = b
                    pad.clear()
                    pad.refresh(0,0,1,1,curses.LINES-2,80)
                    break
                else:
                    if k==460: # somehow this is the code for double quote
                        k = 34
                    if k==530: # somehow this is the code for single quote
                        k = 39
                        
                    ser.receive(k)

            if padNeedsRefresh:
                pad.clear()
                pad.border()
                for line in text[-10::]:
                    pad.addstr(line)
                pad.refresh(0,0,1,1,curses.LINES-2,80)
                padNeedsRefresh=False

        return "ok"
    return ret

def start(debugger):
    #curses.wrapper(main) #this crashes
    scr = curses.initscr()
    curses.cbreak()
    scr.keypad(True)
    try:
        curses.start_color()
    except:
        pass
    main(scr, debugger)
    curses.endwin()

if __name__ == '__main__':
    #curses.wrapper(main) #this crashes
    scr = curses.initscr()
    curses.cbreak()
    scr.keypad(True)
    try:
        curses.start_color()
    except:
        pass
    main(scr)
    curses.endwin()
    