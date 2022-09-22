class QueueOverflowError(Exception):
    def __init__(self, message):
        self.message = message

class ReceiveBuffOverError(Exception):
    def __init__(self, message):
        self.message = message

class ThreadPoolIsShutdown(Exception):
    def __init__(self, message):
        self.message = message

class RpcSendNESTimeOutError(Exception):
    def __init__(self, message):
        self.message = message

class CallRpcTimeOutError(Exception):
    def __init__(self, message):
        self.message = message

class RpcFuncNotFundError(Exception):
    def __init__(self, message):
        self.message = message

class RpcError(Exception):
    def __init__(self, message):
        self.message = message