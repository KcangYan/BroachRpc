"""
线程池队列长度溢出异常
"""
class QueueOverflowError(Exception):
    def __init__(self, message):
        self.message = message

"""
接收udp报文缓冲区溢出异常
"""
class ReceiveBuffOverError(Exception):
    def __init__(self, message):
        self.message = message

"""
线程池已停止
"""
class ThreadPoolIsShutdown(Exception):
    def __init__(self, message):
        self.message = message
"""
NES消息发送超时
"""
class RpcSendNESTimeOutError(Exception):
    def __init__(self, message):
        self.message = message
"""
rpc远程调用响应超时
"""
class CallRpcTimeOutError(Exception):
    def __init__(self, message):
        self.message = message
"""
rpc远程调用远程服务端无此函数
"""
class RpcFuncNotFundError(Exception):
    def __init__(self, message):
        self.message = message
"""
rpc调用通用异常
"""
class RpcError(Exception):
    def __init__(self, message):
        self.message = message