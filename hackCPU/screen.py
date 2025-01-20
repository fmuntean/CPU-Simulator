"""
hack Computer Screen 

video memory starts at 16384 and is 8K long
512x256 pixels
monocrome (1 pixel per bit)

each line is 32 bytes from top to bottom


"""


from re import escape
import threading
import pygame

# Set the screen dimensions
screen_width = 512
screen_height = 256



import pygame
import threading
import sys


class Screen:
    def __init__(self, fetchMem, setMem,width=screen_width, height=screen_height):
      self.fetchMem = fetchMem
      self.setMem = setMem
      self.width = width
      self.height = height
      self.running = False  # Flag to control the rendering thread
      self.thread = None  # Thread object for rendering

    
    def refresh(self,screen):
      # Create a surface to represent the monochrome screen
      surface = pygame.Surface((screen_width, screen_height))

      # Lock the surface for pixel access
      surface.lock()

      for y in range(256):
        # Process each bit in the integer
        for x in range(32):  # Each 16-bit integer represents 16 pixels
            addr = 16384+y*32+x
            val = self.fetchMem(addr)
            for i in range(16):
              bit = (val >> (i)) & 1  # Extract the x-th bit (LSB to MSB)
              color = (255, 255, 255) if bit == 0 else (0, 0, 0)  # White for 1, Black for 0
              # Set the pixel color on the surface
              surface.set_at((x*16+i, y), color)

      # Unlock the surface
      surface.unlock()

      # Blit the surface onto the screen
      screen.blit(surface, (0, 0))

    mapKeys={
        'space':32,

        'return':128,
        'backspace':129,
        'left':130,
        'up':131,
        'right':132,
        'down':133,
        'home':134,
        'end':135,
        'page up':136,
        'page down':137,
        'insert':138,
        'delete':139,
        'escape':140,
        'f1': 141,
        'f2':142,
        'f3':143,
        'f4':144,
        'f5':145,
        'f6':146,
        'f7':147,
        'f8':148,
        'f9':149,
        'f10':150,
        'f11':151,
        'f12':152
    }

    
    def render_loop(self):
        """
        The main rendering loop.
        """
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("hack Computer Screen")
        clock = pygame.time.Clock()  # Clock to control frame rate

        # Clear the screen
        screen.fill((0, 0, 0))

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
        
                # Detect when a key is pressed
                if event.type == pygame.KEYDOWN:
                    #print(f"Key pressed: {pygame.key.name(event.key)}")
                    keyName = pygame.key.name(event.key)
                    if keyName in Screen.mapKeys.keys():
                        self.setMem(24576, Screen.mapKeys[keyName])
                    elif len(keyName)==1:
                        keyName = keyName.upper()
                        self.setMem(24576,ord(keyName))
                        

                # Detect when a key is released
                if event.type == pygame.KEYUP:
                    #print(f"Key released: {pygame.key.key_code(event.key)}")
                    self.setMem(24576, 0)

            # Draw the monochrome screen
            self.refresh(screen)

            # Update the display
            pygame.display.flip()

            # Limit to 30 frames per second
            clock.tick(30)

        pygame.quit()

    def start(self):
        """
        Start the rendering thread.
        """
        self.running = True
        self.thread = threading.Thread(target=self.render_loop,name="screen")
        self.thread.start()

    def stop(self):
        """
        Stop the rendering thread and wait for it to finish.
        """
        self.running = False
        if self.thread:
            self.thread.join()
            self.thread = None


# Example Usage
if __name__ == "__main__":
    mem = [0b1100110011110000]*0x7FFF
    screen = Screen(mem)  # Create a screen object

    
    try:
        # Start the screen in a separate thread
        screen.start()

        # Main thread can dynamically update pixel data
        while True:
            for i in range(0x7FFF):
                mem[i] = ~mem[i]
            pass
    except KeyboardInterrupt:
        # Gracefully stop the screen when interrupted
        screen.stop()
        print("Screen stopped.")

 