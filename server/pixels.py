
import asyncio
import logging
from enum import Enum
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



class PixelType(Enum):
    FIXED = 1,
    PULSE = 2,
    BLINK = 3

class Pixels(object):
    BLACK         = PixelColor(  0,   0,   0)
    GREY          = PixelColor(128, 128, 128)
    WHITE         = PixelColor(255, 255, 255)
    
    RED           = PixelColor(255,   0,   0)
    ROSE          = PixelColor(255,   0, 128)
    MAGENTA       = PixelColor(255,   0, 255)
    VIOLET        = PixelColor(128,   0, 255)
    BLUE          = PixelColor(  0,   0, 255)
    AZURE         = PixelColor(  0, 128, 255)
    CYAN          = PixelColor(  0, 255, 255)
    SPRING_GREEN  = PixelColor(  0, 255, 128)
    GREEN         = PixelColor(  0, 255,   0)
    CHARTREUSE    = PixelColor(128, 255,   0)
    YELLOW        = PixelColor(255, 255,   0)
    ORANGE        = PixelColor(255, 128,   0)

    def __init__(self):
        self.loop = None    # The loop gets assigned after instantiation (in the neopixels thread)
        self.pixels = neopixel.NeoPixel(board.D12, 2, brightness=0.1, auto_write=False)
        self.pixel_type = PixelType.FIXED
        self.pixel_color = Pixels.BLACK
    
    def start(self):
        log.debug('Start pixels')
        # asyncio.run_coroutine_threadsafe(self._rainbow_cycle(0.01), self.loop)  # rainbow cycle with 10ms delay per step
    
    def stop(self):
        log.debug('Stop pixels')
        self.loop.call_soon_threadsafe(self._cancel_tasks)
        self.loop.call_soon_threadsafe(self.loop.stop)

    def set_brightness(self, brightness):
        self.pixels.brightness = brightness
    
    def set_state(self, color, pixel_type):
        self.loop.call_soon_threadsafe(self._cancel_tasks)
        self.loop.call_soon_threadsafe(self._set_state, color, pixel_type)
    
    def _set_state(self, color, pixel_type):
        self.pixel_type = pixel_type
        self.pixel_color = color
        
        if pixel_type == PixelType.PULSE:
            asyncio.ensure_future(self._pulse_colors_loop(color, color), loop=self.loop)
        elif pixel_type == PixelType.BLINK:
            asyncio.ensure_future(self._blink_colors_loop(color, color), loop=self.loop)
        else:
            self._update(color, color)
    
    def _reset_state(self):
        self._set_state(self.pixel_color, self.pixel_type)
    
    def set_colors(self, color1, color2, pixel_type, duration):
        self.loop.call_soon_threadsafe(self._cancel_tasks)
        asyncio.run_coroutine_threadsafe(self._set_colors(color1, color2, pixel_type, duration), self.loop)

    async def _set_colors(self, color1, color2, pixel_type, duration):
        if pixel_type == PixelType.PULSE:
            await self._pulse_colors(color1, color2)
        elif pixel_type == PixelType.BLINK:
            await self._blink_colors(color1, color2)
        else:
            self._update(color1, color2)
        
        if duration > 0:
            await asyncio.sleep(duration)
        if duration >= 0:
            self._reset_state()
    
    def _update(self, color1, color2):
        self.pixels[0] = (color1.red, color1.green, color1.blue)
        self.pixels[1] = (color2.red, color2.green, color2.blue)
        self.pixels.show()
    
    def _new_color(self, color, intensity):
        r = int(intensity / 256 * color.red)
        g = int(intensity / 256 * color.green)
        b = int(intensity / 256 * color.blue)
        return PixelColor(r, g, b)
    
    async def _pulse_colors(self, color1, color2):
        for i in range(255, -1, -1):     # Fade out
            new_color1 = self._new_color(color1, i)
            new_color2 = self._new_color(color2, i)
            self._update(new_color1, new_color2)
            await asyncio.sleep(0.002)
        
        await asyncio.sleep(0.2)
        
        for i in range(256):            # Fade in
            new_color1 = self._new_color(color1, i)
            new_color2 = self._new_color(color2, i)
            self._update(new_color1, new_color2)
            await asyncio.sleep(0.002)
    
    async def _pulse_colors_loop(self, color1, color2):
        while True:
            await self._pulse_colors(color1, color2)
            await asyncio.sleep(3)      # Wait 3 seconds before starting the next pulse effect
    
    async def _blink_colors(self, color1, color2):
        for __ in range(3):
            self._update(Pixels.BLACK, Pixels.BLACK)
            await asyncio.sleep(0.2)
            self._update(color1, color2)
            await asyncio.sleep(0.2)
    
    async def _blink_colors_loop(self, color1, color2):
        while True:
            await self._blink_colors(color1, color2)
            await asyncio.sleep(3)      # Wait 3 seconds before starting the next pulse effect
    
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

