
import RPi.GPIO as GPIO

class Buttons(object):
    
    def __init__(self, loop, daapd):
        self.loop = loop
        self.daapd = daapd
    
    def start(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)     # black
        GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)     # yellow
        GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)     # blue
        GPIO.add_event_detect(26,GPIO.RISING,callback=self.play_next)
        GPIO.add_event_detect(16,GPIO.RISING,callback=self.play_prev)
        GPIO.add_event_detect(20,GPIO.RISING,callback=self.toggle_playpause)
        
    def play_next(self, __):
        self.loop.call_soon_threadsafe(self.daapd.next)
    
    def play_prev(self, __):
        self.loop.call_soon_threadsafe(self.daapd.previous)
    
    def toggle_playpause(self, __):
        pass