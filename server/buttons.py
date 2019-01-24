import asyncio
import logging
import RPi.GPIO as GPIO
from time import sleep, time
import board
import neopixel

log = logging.getLogger('main')

class Buttons(object):
    
    def __init__(self, loop, daapd):
        self.loop = loop
        self.daapd = daapd
        self.last_next_event = 0
        self.last_prev_event = 0
        self.pixels = neopixel.NeoPixel(board.D12, 2, brightness=0.1, auto_write=False)
    
    def start(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)     # yellow
        GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)     # blue
        GPIO.add_event_detect(26, GPIO.FALLING, callback=self.play_next, bouncetime=500)
        GPIO.add_event_detect(16, GPIO.FALLING, callback=self.play_prev, bouncetime=500)
        
        self.rainbow_cycle(0.01) # rainbow cycle with 10ms delay per step

    def rainbow_cycle(self, wait):
        for j in range(255):
            for i in range(2):
                pixel_index = (i * 256 // 2) + j
                self.pixels[i] = self.wheel(pixel_index & 255)
            self.pixels.show()
            sleep(wait)
        sleep(2)
        self.pixels.brightness = 0.2
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

    def play_next(self, pin):
        log.debug('Button pressed on GPIO{}'.format(pin))
        if time() - self.last_next_event < 0.5:
            return

        self.pixels.brightness = 0.6
        self.pixels[0] = (0, 0, 0)
        self.pixels[1] = (51, 204, 255)
        self.pixels.show()
        button_pressed = True
        cycles_pressed = 0
        while button_pressed:
            sleep(0.5)
            self.last_next_event = time()
            cycles_pressed += 1
            if cycles_pressed > 3:
                log.debug('^^^ Volume up ({})'.format(cycles_pressed))
                future = asyncio.run_coroutine_threadsafe(self.daapd.volume_up(5), self.loop)
                log.debug('    result={}'.format(future.result()))
            button_pressed = GPIO.input(26) == GPIO.LOW
        if cycles_pressed <= 3:
            log.debug('>>> Next track ({})'.format(cycles_pressed))
            future = asyncio.run_coroutine_threadsafe(self.daapd.next(), self.loop)
            log.debug('    result={}'.format(future.result()))
        self.last_next_event = time()
        log.debug('<<< GPIO{}'.format(pin))
        self.pixels.brightness = 0.1
        self.pixels.fill((255,255,255))
        self.pixels.show()
    
    def play_prev(self, pin):
        log.debug('Button pressed on GPIO{}'.format(pin))
        if time() - self.last_prev_event < 0.5:
            return

        self.pixels.brightness = 0.6
        self.pixels[0] = (255, 255, 0)
        self.pixels[1] = (0, 0, 0)
        self.pixels.show()
        button_pressed = True
        cycles_pressed = 0
        while button_pressed:
            sleep(0.5)
            self.last_prev_event = time()
            cycles_pressed += 1
            if cycles_pressed > 3:
                log.debug('___ Volume down ({})'.format(cycles_pressed))
                future = asyncio.run_coroutine_threadsafe(self.daapd.volume_down(5), self.loop)
                log.debug('    result={}'.format(future.result()))
            button_pressed = GPIO.input(16) == GPIO.LOW
        if cycles_pressed <= 3:
            log.debug('<<< Previous track ({})'.format(cycles_pressed))
            future = asyncio.run_coroutine_threadsafe(self.daapd.previous(), self.loop)
            log.debug('    result={}'.format(future.result()))
        self.last_prev_event = time()
        log.debug('<<< GPIO{}'.format(pin))
        self.pixels.brightness = 0.1
        self.pixels.fill((255,255,255))
        self.pixels.show()
    
    def toggle_playpause(self, pin):
        log.debug('Button pressed on GPIO{}'.format(pin))
