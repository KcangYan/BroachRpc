from network import RpcHandler
from threadPool import BroachPool
import socket
import logging

class RpcClient:

    def __init__(self):
        self.id = RpcHandler.getId()
        self.pool = BroachPool.BroachPool

    @staticmethod
    def __send(data, ip, port):
        addr = (ip, port)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(data, addr)
        logging.debug("发送消息 -> "+str(addr)+" 内容: "+data)
        s.close()

    def sendCIM(self, msg, ip, port):
        data = RpcHandler.getCIM(self.id, msg)
        self.__send(data, ip, port)

    def sendNCP(self, msgId, isS, ip, port):
        data = RpcHandler.getNCP(self.id, msgId, isS)
        self.__send(data, ip, port)


Client = RpcClient()

