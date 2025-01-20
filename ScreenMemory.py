
import curses

from debuggerCli import Debugger

class ScreenMemory:
    def __init__(self,screen):
        self.screen = screen
        self.resize()

    def resize(self):
        #we calculate how many columns/pads we can fit in the screen
        lines,cols = self.screen.getmaxyx()
        # each memory block is 8 lines x 30 columns displaying the Address: 8 bytes per line (4+:+_+ (2+_)*8)
        # each memory block is 8 lines x 46 columns displaying the Address: 8 words per line (4+:+_+ (4+_)*8) = 6+ 8*5=46
        pads = cols // 50
        self.pads = []
        for i in range(0,pads):
            self.pads.append(curses.newpad(8,50))

    def refresh(self,debugger:Debugger):
        for i,p in enumerate(self.pads):
            p.clear()
            startAddr = debugger.displayStart+i*64
            mem = debugger.get_mem(startAddr,64)
            line = 0
            while line<8:
                text = f"{startAddr+line*8:04X}: {' '.join(f"{int(m):04X}" for m in mem[line*8:line*8+8])}"
                p.addstr(line,0,text)
                line+=1
            #for c,s in enumerate(text):
            #    p.addstr(c,0,s)
                #p.clrtoeol()
            #p.clrtobot()
            #p.border()
            #p.refresh(0,0,1,1+i*32,10,1+i*32+32)
            p.refresh(0,0,1,1+i*52,10,1+i*52+52)
    
    def getBlockSize(self):
        return len(self.pads)*64
    