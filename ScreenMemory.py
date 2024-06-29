
import curses

from debugger import Debugger

class ScreenMemory:
    def __init__(self,screen):
        self.screen = screen
        self.resize()

    def resize(self):
        #we calculate how many columns/pads we can fit in the screen
        lines,cols = self.screen.getmaxyx()
        # each memory block is 8 lines x 30 columns displaying the Address: 8 bytes per line
        pads = cols // 34
        self.pads = []
        for i in range(0,pads):
            self.pads.append(curses.newpad(8,30))

    def refresh(self,debugger:Debugger):
        for i,p in enumerate(self.pads):
            p.clear()
            text = debugger.list_mem(debugger.displayStart+i*64,64)
            for c,s in enumerate(text):
                p.addstr(c,0,s)
                #p.clrtoeol()
            #p.clrtobot()
            #p.border()
            p.refresh(0,0,1,1+i*32,10,1+i*32+32)
    
    def getBlockSize(self):
        return len(self.pads)*64
    