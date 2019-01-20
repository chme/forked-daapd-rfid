import asyncio
import RPi.GPIO as GPIO
from time import sleep, time

class Buttons(object):
    
    def __init__(self, loop, daapd):
        self.loop = loop
        self.daapd = daapd
        self.last_next_event = 0
        self.last_prev_event = 0
    
    def start(self):
        GPIO.setmode(GPIO.BCM)
#        GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)     # black
        GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)     # yellow
        GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)     # blue
        GPIO.add_event_detect(26, GPIO.FALLING, callback=self.play_next, bouncetime=500)
        GPIO.add_event_detect(16, GPIO.FALLING, callback=self.play_prev, bouncetime=500)
#        GPIO.add_event_detect(20, GPIO.FALLING, callback=self.toggle_playpause)
        


    def play_next(self, pin):
        print('Button pressed on GPIO{}'.format(pin))
#        GPIO.remove_event_detect(26)
        if time() - self.last_next_event < 0.5:
            return

        button_pressed = True
        cycles_pressed = 0
        while button_pressed:
            sleep(0.5)
            self.last_next_event = time()
            cycles_pressed += 1
            if cycles_pressed > 3:
                print('^^^ Volume up ({})'.format(cycles_pressed))
                future = asyncio.run_coroutine_threadsafe(self.daapd.volume_up(5), self.loop)
                print(future.result())
            button_pressed = GPIO.input(26) == GPIO.LOW
        if cycles_pressed <= 3:
            print('>>> Next track ({})'.format(cycles_pressed))
            future = asyncio.run_coroutine_threadsafe(self.daapd.next(), self.loop)
            print(future.result())
#        GPIO.add_event_detect(26, GPIO.FALLING, callback=self.play_next, bouncetime=600)
        self.last_next_event = time()
        print('<<< GPIO{}'.format(pin))
    
    def play_prev(self, pin):
        print('Button pressed on GPIO{}'.format(pin))
        if time() - self.last_prev_event < 0.5:
            return

        button_pressed = True
        cycles_pressed = 0
        while button_pressed:
            sleep(0.5)
            self.last_prev_event = time()
            cycles_pressed += 1
            if cycles_pressed > 3:
                print('___ Volume down ({})'.format(cycles_pressed))
                future = asyncio.run_coroutine_threadsafe(self.daapd.volume_down(5), self.loop)
                print(future.result())
            button_pressed = GPIO.input(16) == GPIO.LOW
        if cycles_pressed <= 3:
            print('<<< Previous track ({})'.format(cycles_pressed))
            future = asyncio.run_coroutine_threadsafe(self.daapd.previous(), self.loop)
            print(future.result())
        self.last_prev_event = time()
        print('<<< GPIO{}'.format(pin))
    
    def toggle_playpause(self, pin):
        print('Button pressed on GPIO{}'.format(pin))
