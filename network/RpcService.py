from common import CommonDef
from network import RpcServer,RpcClient
import threading
import logging
import json

"""
rpc 应用通信协议 json
{
  "funcId": "" , 远程调用函数id
  "args": "", 参数
  "kwargs": "", 参数
  "reqId": "0 18", 请求报文id
  "orgId": "0 18", 响应原报文id 无的话就是0
  "status": "", 处理状态
  "return": "" 远程调用返回值
}
"""

@CommonDef.singleton
class RpcService:
    def __init__(self):
        self.__NCPRev = {}  # 响应NCP消息
        self.__NCPRevLock = threading.RLock()
        self.rpcClient = RpcClient.RpcClient(self.__NCPRev, self.__NCPRevLock)
        self.rpcServer = RpcServer.RpcServer(self.rpcClient)

    def serverStart(self):
        self.rpcServer.start()

    def sendTo(self, msg:dict, ip: str, port: int):
        jsonStr = json.dumps(msg)



instance = RpcService()
