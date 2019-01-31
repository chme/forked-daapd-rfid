
import asyncio
import logging
from time import sleep
from enum import Enum

import board
import neopixel


log = logging.getLogger('main')

class PixelColors(Enum):
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    YELLOW = (51, 204, 255)
    BLUE = (255, 255, 0)

class Pixels(object):

    def __init__(self):
        self.loop = None
        self.pixels = neopixel.NeoPixel(board.D12, 2, brightness=0.1, auto_write=False)
    
    async def start(self, loop):
        self.loop = loop
        self.rainbow_cycle(0.01) # rainbow cycle with 10ms delay per step
    
    def set_fill(self, color, brightness=0.1):
        asyncio.run_coroutine_threadsafe(self._set_fill(color, brightness=brightness), self.loop)
    
    def set_colors(self, color1, color2, brightness=0.1):
        asyncio.run_coroutine_threadsafe(self._set_colors(color1, color2, brightness=brightness), self.loop)

    async def _set_fill(self, color, brightness=0.1):
        self.pixels.brightness = brightness
        self.pixels.fill(color.value)
        self.pixels.show()
    
    async def _set_colors(self, color1, color2, brightness=0.1):
        self.pixels.brightness = brightness
        self.pixels[0] = color1.value
        self.pixels[1] = color2.value
        self.pixels.show()
    
    def rainbow_cycle(self, wait):
        for j in range(255):
            for i in range(2):
                pixel_index = (i * 256 // 2) + j
                self.pixels[i] = self.wheel(pixel_index & 255)
            self.pixels.show()
            sleep(wait)
        self.pixels.brightness = 0.1
        self.pixels.fill((255,255,255))
        self.pixels.show()

    def wheel(self, pos):
        # Input a value 0 to 255 to get a color value.
        # The colours are a transition r - g - b - back to r.
        if pos < 0 or pos > 255:
            r = g = b = 0
        elif pos < 85:
            r = int(pos * 3)
            g = int(255 - pos*3)
            b = 0
        elif pos < 170:
            pos -= 85
            r = int(255 - pos*3)
            g = 0
            b = int(pos*3)
        else:
            pos -= 170
            r = 0
            g = int(pos*3)
            b = int(255 - pos*3)
        return (r, g, b)


def neopixels(pixels):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(pixels.start(loop))
    loop.run_forever()

