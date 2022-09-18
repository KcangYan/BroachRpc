from network import RpcHandler
from threadPool.ThreadPool import *
import socket
import logging

class RpcClient:

    def __init__(self):
        self.id = RpcHandler.getId()
        self.pool = CreatePool(core=2, max=10,
                        poolName="rpcClient", sleepTime=10,
                        queue=ArrayQueue(queueMax=100, createThreadThreshold=5))

    def __send(self, data, ip, port):
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

