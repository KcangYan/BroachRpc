from network import RpcHandler
from config import GlobalVariable
from exception import DefException
import socket
import logging
import time

class RpcClient:

    def __init__(self):
        self.pool = GlobalVariable.BroachPool
        self.stepTime = 0.15 # 重传间隔

    @staticmethod
    def __send(data, ip, port):
        addr = (ip, port)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if len(data) > RpcHandler.bufferLen :
            raise IOError("发送消息超过缓冲区3028字节长度限制")
        s.sendto(data, addr)
        logging.debug("发送消息 -> "+str(addr)+" 内容: "+data.decode("utf-8"))
        s.close()

    def sendCIM(self, msg, ip, port):
        data = RpcHandler.getCIM(msg)
        self.__send(data, ip, port)

    def sendNCP(self, msgId, isS, ip, port):
        data = RpcHandler.getNCP(msgId, isS)
        self.__send(data, ip, port)

    def sendNES(self, msgId, msg, ip, port):
        if RpcHandler.NCPRev.get(msgId) is not None:
            return "idRepeat"
        msgDict, msgInfoList = RpcHandler.getNES(msgId, GlobalVariable.params["params"]["rpcIp"],
                                    GlobalVariable.params["params"]["rpcPort"], msg)
        for key in msgDict:
            self.__send(msgDict[key], ip, port)

        udpTimeOut = int(GlobalVariable.params["params"]["udpTimeOut"])
        timeUse = 0
        while timeUse <= udpTimeOut:
            revInfoList = RpcHandler.NCPRev.get(msgId)
            if revInfoList is None:
                time.sleep(self.stepTime)
                timeUse = timeUse + self.stepTime
                continue
            for revInfo in revInfoList:
                msgInfo = revInfo[0]
                isS = revInfo[1]
                if isS == "0":
                    msgInfoList.remove(msgInfo)
                elif isS == "2":
                    #id重复 报错 重发
                    with RpcHandler.NCPRevLock:
                        RpcHandler.NCPRev.pop(msgId)
                    return "idRepeat"
            if len(msgInfoList) == 0:
                break

            time.sleep(self.stepTime)
            timeUse = timeUse + self.stepTime

            revInfoList = RpcHandler.NCPRev[msgId]
            if revInfoList is None:
                continue
            for revInfo in revInfoList:
                msgInfo = revInfo[0]
                isS = revInfo[1]
                if isS == "0":
                    msgInfoList.remove(msgInfo)
                elif isS == "2":
                    #id重复 报错 重发
                    with RpcHandler.NCPRevLock:
                        RpcHandler.NCPRev.pop(msgId)
                    return "idRepeat"
            if len(msgInfoList) == 0:
                break

            for key in msgInfoList:
                self.__send(msgDict[key], ip, port)
        with RpcHandler.NCPRevLock:
            RpcHandler.NCPRev.pop(msgId)

        if timeUse > udpTimeOut:
            raise DefException.RpcSendNESTimeOutError("发送响应超时")



Client = RpcClient()

