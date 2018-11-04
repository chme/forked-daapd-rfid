
import time
import threading

class SimpleMFRC522:

    irq = threading.Event()

    def __init__(self):
        pass

    def cancel(self):
        self.irq.set()

    def wait_for_tag_available(self):
        ##pass
        self.irq.clear()
        waiting = True
        while waiting:
            waiting = not self.irq.wait(5)
        self.irq.clear()

    def read(self):
        return 123, 'text'

    def read_id(self):
        return 123, 123456

    def read_content(self, uid):
        return 'text_read'

    def write(self, uid, text):
        return 123, 'text'

    def uid_to_num(self, uid):
        n = 0
        for i in range(0, 5):
            n = n * 256 + uid[i]
        return n
