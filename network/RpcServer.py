from config import ConfigScan
import socket
import logging
from threadPool import ThreadPool

config = ConfigScan.Config("../application.json")

class RpcServer:
    def __init__(self, config:ConfigScan.Config):
        self.config = config
        self.address=(config.getParam("rpcIp"),config.getParam("rpcPort"))
        self.recvLen = 1024
        self.threadPool = ThreadPool.CreatePool(core=1, max=10, poolName="rpcServer", sleepTime=10,
                                                queue=ThreadPool.ArrayQueue(queueMax=100, createThreadThreshold=5))
    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(self.address)
        logging.info("rpc 服务端口启动 -> "+str(self.address))
        while True:
            try:
                data, addr = s.recvfrom(self.recvLen)
                logging.debug("got data from -> " + str(addr))
                logging.debug("got data -> " + data.decode("utf-8"))
                self.threadPool.submit(self.__msgHandler, data, addr)
            except :
                logging.exception(exc_info=True, msg="rpc 通信异常")

    def __msgHandler(self, data, addr):
        logging.info("got data from -> " + str(addr))
        logging.info("got data -> " + data.decode("utf-8"))
