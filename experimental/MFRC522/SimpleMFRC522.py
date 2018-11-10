
import time
import threading

class SimpleMFRC522:

    irq = threading.Event()

    def __init__(self):
        pass

    def cancel_wait(self):
        self.irq.set()

    def wait_for_tag_available(self):
        ##pass
        self.irq.clear()
        waiting = True
        while waiting:
            waiting = not self.irq.wait(5)
        self.irq.clear()

    def wait_for_tag_removed(self):
        pass

    def read(self):
        return 123456, 'text'

    def read_id(self):
        return 123456

    def read_content(self, uid):
        return 'text_read'

    def write(self, uid, text):
        return 'text'

    def uid_to_num(self, uid):
        n = 0
        for i in range(0, 5):
            n = n * 256 + uid[i]
        return n
