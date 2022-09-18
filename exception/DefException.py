class QueueOverflowError(Exception):
    def __init__(self, message):
        self.message = message

class ReceiveBuffOverError(Exception):
    def __init__(self, message):
        self.message = message

class ThreadPoolIsShutdown(Exception):
    def __init__(self, message):
        self.message = message