from network import RpcHandler
from config import GlobalVariable
import socket
import logging

class RpcClient:

    def __init__(self):
        self.id = RpcHandler.getId()
        self.pool = GlobalVariable.BroachPool
        self.stepTime = 0.15 # 重传间隔

    @staticmethod
    def __send(data, ip, port):
        addr = (ip, port)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if len(data) > 3028 :
            raise IOError("发送消息超过缓冲区3028字节长度限制")
        s.sendto(data, addr)
        logging.debug("发送消息 -> "+str(addr)+" 内容: "+data)
        s.close()

    def sendCIM(self, msg, ip, port):
        data = RpcHandler.getCIM(self.id, msg)
        self.__send(data, ip, port)

    def sendNCP(self, msgId, isS, ip, port):
        data = RpcHandler.getNCP(self.id, msgId, isS)
        self.__send(data, ip, port)

    def sendNES(self, msg, ip, port):
        msgList, msgIdList = RpcHandler.getNES(self.id, GlobalVariable.params["params"]["rpcIp"],
                                    GlobalVariable.params["params"]["rpcPort"], msg)
        for item in msgList:
            self.__send(item, ip, port)

        udpTimeOut = int(GlobalVariable.params["params"]["udpTimeOut"])



Client = RpcClient()

