from config import GlobalVariable
import socket
import logging

class RpcServer:
    def __init__(self):
        self.address=(GlobalVariable.params["params"]["rpcIp"], GlobalVariable.params["params"]["rpcPort"])
        self.recvLen = 1024
        self.threadPool = GlobalVariable.BroachPool
    def start(self):
        self.threadPool.submit(self.__serverRun)

    def __serverRun(self):
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

    @staticmethod
    def __msgHandler(data, addr):
        logging.info("got data from -> " + str(addr))
        logging.info("got data -> " + data.decode("utf-8"))
