from threading import Thread
import time
from ScreenMemory import ScreenMemory
import mc6800
import debugger
#from acia import UART
from st16c1550 import UART

import curses

mem = bytearray(0xFFFF+1) # 64KB


ser = UART(0xFFF0) # Serial 


def fetchMemory(address):
    if (ser.match(address)):
        return ser.read(address)
    else:
        return mem[address & 0xFFFF]

def setMemory(address, value):
    if (ser.match(address)):
        ser.write(address,value)
    else:
        mem[address & 0xFFFF] = value

#debugger.loadHex(mem,"mc6802.hex")
debugger.loadHex(mem,"swtb2.hex")
debugger.loadHex(mem,"TB_6800.hex")

cpu = mc6800.MC6800(fetchMemory,setMemory)

debugger = debugger.Debugger(cpu,mem)

def topRefresh(screen,padTop,debugger):
    y, x = screen.getmaxyx()
    padTop.clear()
    topStr = f"{debugger.list_regs(cpu)}| |{debugger.get_opcodes(cpu.PC)}| {debugger.list_cmd(cpu.PC)}"
    padTop.addstr(topStr)
    padTop.refresh(0,0,0,0,0, x-1 )

cmdPrompt = "> "

def main(screen):
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

        winMem.refresh(mem,debugger)
        
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
                winMem.refresh(mem,debugger)
                
                #winTop.resize(1,x) # curses.newwin(1,x,0,0)
                winBot.resize(1,x) # curses.newwin(1,x,11,0)
                
                topRefresh(screen,padTop,debugger)
                break
            if (ch != None) & (ch < 128) & (ch >=0):
                cmdDebug+=chr(ch)

                
            

        if cmdDebug.lower() == "exit" or cmdDebug.lower() == "quit" or cmdDebug.lower() == 'q':
            break
        
        #screen.refresh()
        ret = executeCommand(cmdDebug)    

        if ret != None:    
            winBot.addstr("  "+ret)
            winBot.refresh()
        else:    
            time.sleep(1)

        #screen.refresh()
        
def executeCommand(cmdDebug):
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
    