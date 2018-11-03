
class SimpleMFRC522:

    def __init__(self):
        pass

    def wait_for_tag(self):
        pass

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
