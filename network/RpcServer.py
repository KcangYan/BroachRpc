from config import GlobalVariable
from network import RpcHandler, RpcClient
import socket
import logging

class RpcServer:
    def __init__(self):
        self.address=(GlobalVariable.params["params"]["rpcIp"], GlobalVariable.params["params"]["rpcPort"])
        self.recvLen = RpcHandler.bufferLen
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
                self.threadPool.submit(self.__msgHandler, data, addr)
            except :
                logging.exception(exc_info=True, msg="rpc 通信异常")

    def __msgHandler(self, data, addr):
        logging.debug("got data from -> " + str(addr))
        logging.debug("got data -> " + data.decode("utf-8"))
        msgType, msg = RpcHandler.decodeData(data)
        if msgType == "NCP":
            self.__NCPHandler(msg)
        elif msgType == "NES":
            self.__NESHandler(msg)

    def __NCPHandler(self, msg):
        msgId, msgInfo, isS = RpcHandler.decodeNCP(msg)
        with RpcHandler.NCPRevLock:
            if RpcHandler.NCPRev.get(msgId) is None:
                msgInfoList = [[msgInfo, isS]]
                RpcHandler.NCPRev[msgId] = msgInfoList
            else:
                RpcHandler.NCPRev[msgId].append([msgInfo, isS])

    def __NESHandler(self, msg):
        msgId, msgInfo, revIp, revPort, msgPart = RpcHandler.decodeNES(msg)
        msgOrder = int(msgInfo[5:10])
        with RpcHandler.NESRevLock:
            msgPartDict = RpcHandler.NESRev.get(msgId)
            if msgPartDict is None:
                RpcHandler.NESRev[msgId] = { msgOrder:msgPart, "msgLen": msgInfo[0:5] }
                RpcClient.Client.sendNCP(msgId+msgInfo, "0", revIp, revPort)
            else:
                if msgPartDict.get(msgOrder) is None:
                    msgPartDict[msgOrder] = msgPart
                    RpcClient.Client.sendNCP(msgId+msgInfo, "0", revIp, revPort)
                else:
                    if msgPartDict[msgOrder] == msgPart:
                        RpcClient.Client.sendNCP(msgId+msgInfo, "0", revIp, revPort)
                    else:
                        RpcClient.Client.sendNCP(msgId+msgInfo, "2", revIp, revPort)
        msgPartDict = RpcHandler.NESRev.get(msgId)
        if len(msgPartDict) == msgOrder:
            #收到完整NES消息通知上游处理
            pass

