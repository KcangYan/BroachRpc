from config import GlobalVariable
from network import RpcHandler, RpcClient
import socket
import logging
import time

class RpcServer:
    def __init__(self):
        self.address=(GlobalVariable.params["params"]["rpcIp"], GlobalVariable.params["params"]["rpcPort"])
        self.recvLen = RpcHandler.bufferLen
        self.threadPool = GlobalVariable.BroachPool
        self.callBackNES = []
    def start(self):
        self.threadPool.submit(self.__serverRun)

    def addNESCallBack(self, fn):
        self.callBackNES.append(fn)

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
        msgLen = int(msgInfo[0:5])
        if msgLen == 1:
            #无分段消息
            RpcClient.Client.sendNCP(msgId+msgInfo, "0", revIp, revPort)
            for fn in self.callBackNES:
                self.threadPool.submit(fn, msgPart.decode("utf-8"), revIp, int(revPort))
            return
        with RpcHandler.NESRevLock:
            msgPartDict = RpcHandler.NESRevPart.get(msgId)
            if msgPartDict is None:
                if RpcHandler.NESRev.get(msgId) is None:
                    RpcHandler.NESRevPart[msgId] = { msgOrder:msgPart, "msgLen": msgLen }
                RpcClient.Client.sendNCP(msgId+msgInfo, "0", revIp, revPort)
            else:
                if msgPartDict.get(msgOrder) is None:
                    msgPartDict[msgOrder] = msgPart
                    RpcClient.Client.sendNCP(msgId+msgInfo, "0", revIp, revPort)
                else:
                    if msgPartDict[msgOrder] == msgPart:
                        RpcClient.Client.sendNCP(msgId+msgInfo, "0", revIp, revPort)
                    else:
                        #RpcHandler.NESRevPart.pop(msgId)
                        RpcClient.Client.sendNCP(msgId+msgInfo, "2", revIp, revPort)
            msgPartDict = RpcHandler.NESRevPart.get(msgId)
            if (len(msgPartDict)-1) == msgLen:
                revMsg = b""
                for i in range(0, msgLen):
                    revMsg = revMsg + msgPartDict[i]
                #RpcHandler.NESRev[msgId] = {"msg": revMsg, "time":time.time()}
                #通知上游函数处理
                for fn in self.callBackNES:
                    self.threadPool.submit(fn, revMsg.decode("utf-8"), revIp, int(revPort))
                #    fn(revMsg.decode("utf-8"))
                #删除片段中的NES消息
                RpcHandler.NESRevPart.pop(msgId)

