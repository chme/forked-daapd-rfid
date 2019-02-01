
import asyncio
import logging

import board
import neopixel


log = logging.getLogger('main')

class PixelColor(object):
    
    def __init__(self, red, green, blue):
        self.red   = red
        self.green = green
        self.blue  = blue

    def __str__(self):
        return 'PixelColor(r={},g={},b={}) '.format(self.red, self.green, self.blue)


BLACK   = PixelColor(  0,   0,   0)
WHITE   = PixelColor(255, 255, 255)
RED     = PixelColor(255,   0,   0)
GREEN   = PixelColor(  0, 255,   0)
BLUE    = PixelColor(  0,   0, 255)
YELLOW  = PixelColor(255, 255,   0)

class Pixels(object):

    def __init__(self):
        self.loop = None
        self.current_task = None
        self.pixels = neopixel.NeoPixel(board.D12, 2, brightness=0.1, auto_write=False)
    
    def start(self):
        log.debug('Start pixels')
        asyncio.run_coroutine_threadsafe(self._rainbow_cycle(0.01), self.loop)  # rainbow cycle with 10ms delay per step
    
    def stop(self):
        log.debug('Stop pixels')
        self.loop.call_soon_threadsafe(self._cancel_tasks)
        self.loop.call_soon_threadsafe(self.loop.stop)

    def set_fill(self, color):
        log.debug('Set fill color')
        self.loop.call_soon_threadsafe(self._cancel_tasks)
        self.loop.call_soon_threadsafe(self._set_fill, color)
        # asyncio.run_coroutine_threadsafe(self._set_fill(color, brightness=brightness), self.loop)
    
    def set_colors(self, color1, color2):
        log.debug('Set colors')
        self.loop.call_soon_threadsafe(self._cancel_tasks)
        self.loop.call_soon_threadsafe(self._set_colors, color1, color2)
        # asyncio.run_coroutine_threadsafe(self._set_colors(color1, color2, brightness=brightness), self.loop)
    
    def pulse_color(self, color):
        log.debug('Pulse')
        self.loop.call_soon_threadsafe(self._cancel_tasks)
        asyncio.run_coroutine_threadsafe(self._pulse_color(color), self.loop)

    def pulse_color_loop(self, color):
        log.debug('Pulse loop')
        self.loop.call_soon_threadsafe(self._cancel_tasks)
        asyncio.run_coroutine_threadsafe(self._pulse_color_loop(color), self.loop)
    
    def _set_fill(self, color, brightness=0.1):
        # log.debug('>> fill {}'.format(color))
        self.pixels.brightness = brightness
        self.pixels.fill((color.red, color.green, color.blue))
        self.pixels.show()
    
    def _set_colors(self, color1, color2, brightness=0.1):
        # log.debug('>> colors {}, {}'.format(color1,color2))
        self.pixels.brightness = brightness
        self.pixels[0] = (color1.red, color1.green, color1.blue)
        self.pixels[1] = (color2.red, color2.green, color2.blue)
        self.pixels.show()
    
    async def _pulse_color(self, color):
        # log.debug('>> pulse')
        
        # log.debug('>> pulse >> fade out')
        for i in range(255, -1, -1):     # Fade out
            r = int(i / 256 * color.red)
            g = int(i / 256 * color.green)
            b = int(i / 256 * color.blue)
            self._set_fill(PixelColor(r, g, b))
            await asyncio.sleep(0.001)
        
        # log.debug('>> pulse >> fade in')
        for i in range(256):            # Fade in
            r = int(i / 256 * color.red)
            g = int(i / 256 * color.green)
            b = int(i / 256 * color.blue)
            self._set_fill(PixelColor(r, g, b))
            await asyncio.sleep(0.001)

        # log.debug('>> pulse >> END')
    
    async def _pulse_color_loop(self, color):
        # log.debug('>> pulse loop')
        while True:
            await self._pulse_color(color)
            await asyncio.sleep(0.1)
    
    async def _rainbow_cycle(self, wait):
        log.debug('>> rainbow')
        
        for j in range(255):
            for i in range(2):
                pixel_index = (i * 256 // 2) + j
                self.pixels[i] = self._wheel(pixel_index & 255)
            self.pixels.show()
            await asyncio.sleep(wait)
        
        self.pixels.brightness = 0.1
        self.pixels.fill((255,255,255))
        self.pixels.show()

    def _wheel(self, pos):
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

    def _cancel_tasks(self):
        log.debug('>> CANCEL')
        tasks = asyncio.gather(
                    *asyncio.Task.all_tasks(loop=self.loop),
                    loop=self.loop,
                    return_exceptions=True)
        tasks.cancel()

def neopixels(pixels):
    log.debug('[pixels] Run neopixels')
    loop = asyncio.new_event_loop()
    pixels.loop = loop
    log.debug('[pixels] run forever')
    loop.run_forever()
    log.debug('[pixels] stopped')

