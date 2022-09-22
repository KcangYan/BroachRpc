from common import GlobalVariable, CommonDef
from network import MsgHandler
import socket
import logging
import threading

@CommonDef.singleton
class RpcServer:
    def __init__(self, rpcClient):
        self.address=(GlobalVariable.params["params"]["rpcIp"], GlobalVariable.params["params"]["rpcPort"])
        self.recvLen = GlobalVariable.BufferLen
        self.threadPool = GlobalVariable.BroachPool
        self.__callBackNES = []
        self.__NESRevPart = {} #收集收到的NES消息片段
        self.__NESRevLock = threading.RLock()
        self.__rpcClient = rpcClient
    def start(self):
        self.threadPool.submit(self.__serverRun)

    def addNESCallBack(self, fn):
        self.__callBackNES.append(fn)

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
        msgType, msg = MsgHandler.decodeData(data)
        if msgType == "NCP":
            self.__NCPHandler(msg)
        elif msgType == "NES":
            self.__NESHandler(msg)

    def __NCPHandler(self, msg):
        msgId, msgInfo, isS = MsgHandler.decodeNCP(msg)
        self.__rpcClient.handlerNCP(msgId, msgInfo, isS)

    def __NESHandler(self, msg):
        msgId, msgInfo, revIp, revPort, msgPart = MsgHandler.decodeNES(msg)
        msgOrder = int(msgInfo[5:10])
        msgLen = int(msgInfo[0:5])
        if msgLen == 1:
            #无分段消息
            self.__rpcClient.sendNCP(msgId+msgInfo, "0", revIp, revPort)
            for fn in self.__callBackNES:
                self.threadPool.submit(fn, msgPart.decode("utf-8"), revIp, int(revPort))
            return
        with self.__NESRevLock:
            msgPartDict = self.__NESRevPart.get(msgId)
            if msgPartDict is None:
                self.__NESRevPart[msgId] = {msgOrder:msgPart, "msgLen": msgLen}
                self.__rpcClient.sendNCP(msgId+msgInfo, "0", revIp, revPort)
            else:
                if msgPartDict.get(msgOrder) is None:
                    msgPartDict[msgOrder] = msgPart
                    self.__rpcClient.sendNCP(msgId+msgInfo, "0", revIp, revPort)
                else:
                    if msgPartDict[msgOrder] == msgPart:
                        self.__rpcClient.Client.sendNCP(msgId+msgInfo, "0", revIp, revPort)
                    else:
                        #RpcHandler.NESRevPart.pop(msgId)
                        self.__rpcClient.sendNCP(msgId+msgInfo, "2", revIp, revPort)
            msgPartDict = self.__NESRevPart.get(msgId)
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
                self.__NESRevPart.pop(msgId)

