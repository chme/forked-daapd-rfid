import asyncio
import logging
import RPi.GPIO as GPIO
from time import sleep, time
import board
import neopixel


log = logging.getLogger('main')


class LongPressButton(object):
    
    def __init__(self, pin, name=None, bouncetime=1.0, on_pressed_cb=None, on_released_cb=None, short_press_cb=None, short_press_time=1.0, long_press_cb=None, long_press_cb_trigger_time=0.5):
        self.pin = pin
        self.bouncetime = bouncetime
        self.on_pressed_cb = on_pressed_cb
        self.on_released_cb = on_released_cb
        self.short_press_cb = short_press_cb
        self.short_press_time = short_press_time
        self.long_press_cb = long_press_cb
        self.long_press_cb_trigger_time = long_press_cb_trigger_time
        self.name = name if name else 'GPIO{}'.format(pin)
        
        self.last_event_time = 0
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin, GPIO.FALLING, callback=self.__on_event_detect)
    
    def __on_event_detect(self, __):
        if time() - self.last_event_time < self.bouncetime:
            log.debug('[buttons] Ignoring button press on {} (bouncetime)'.format(self.name))
            return
        
        log.debug('[buttons] Button press on {}'.format(self.name))
        self.last_event_time = time()
        if self.on_pressed_cb:
            self.on_pressed_cb(self.pin)
        
        long_press_time = self.last_event_time + self.short_press_time
        button_pressed = True
        is_short_press = True
        
        while button_pressed:
            sleep(0.1)
            self.last_event_time = time()
            is_short_press = is_short_press and self.last_event_time < long_press_time
            
            # log.debug('[buttons]     Longpress detection: is_short {}, last_event {}, long_press {}'.format(is_short_press, self.last_event_time, long_press_time))
            if self.long_press_cb and not is_short_press and self.last_event_time > long_press_time:
                self.long_press_cb(self.pin)
                long_press_time = self.last_event_time + self.long_press_cb_trigger_time
            button_pressed = GPIO.input(self.pin) == GPIO.LOW
        
        self.last_event_time = time()
        if is_short_press and self.short_press_cb:
            self.short_press_cb(self.pin)
        if self.on_released_cb:
            self.on_released_cb(self.pin)
        log.debug('[buttons] Button released on {}'.format(self.name))

class Buttons(object):
    
    def __init__(self, loop, daapd, button_next_pin=26, button_prev_pin=16):
        self.loop = loop
        self.daapd = daapd
        self.button_next_pin = button_next_pin
        self.button_prev_pin = button_prev_pin

        GPIO.setmode(GPIO.BCM)
        self.button_next = LongPressButton(self.button_next_pin,
                                           on_pressed_cb=self.__on_pressed, 
                                           on_released_cb=self.__on_released, 
                                           short_press_cb=self.play_next, 
                                           long_press_cb=self.volume_up)
        self.button_prev = LongPressButton(self.button_prev_pin,
                                           on_pressed_cb=self.__on_pressed, 
                                           on_released_cb=self.__on_released, 
                                           short_press_cb=self.play_prev, 
                                           long_press_cb=self.volume_down)
        
        self.pixels = neopixel.NeoPixel(board.D12, 2, brightness=0.1, auto_write=False)
    
    def start(self):
        log.debug('[buttons] Starting buttons controller ...')
        self.rainbow_cycle(0.001) # rainbow cycle with 1ms delay per step
        log.debug('[buttons] Starting buttons controller complete')
    
    def cleanup(self):
        GPIO.cleanup([self.button_next_pin, self.button_prev])

    def __on_pressed(self, pin):
        self.pixels.brightness = 0.1
        self.pixels.fill((0,0,0))
        
        if pin == self.button_next_pin:
            self.pixels[1] = (51, 204, 255)
        elif pin == self.button_prev_pin:
            self.pixels[0] = (255, 255, 0)
        
        self.pixels.show()
    
    def __on_released(self, __):
        self.pixels.brightness = 0.1
        self.pixels.fill((255,255,255))
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

    def play_next(self, __):
        log.debug('[buttons] Play next triggered')
        asyncio.run_coroutine_threadsafe(self.daapd.next(), self.loop)
    
    def volume_up(self, __):
        log.debug('[buttons] Volume up triggered')
        asyncio.run_coroutine_threadsafe(self.daapd.volume_up(5), self.loop)
    
    def play_prev(self, __):
        log.debug('[buttons] Play previous triggered')
        asyncio.run_coroutine_threadsafe(self.daapd.previous(), self.loop)
    
    def volume_down(self, __):
        log.debug('[buttons] Volume down triggered')
        asyncio.run_coroutine_threadsafe(self.daapd.volume_down(5), self.loop)
