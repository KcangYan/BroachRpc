from network import MsgHandler
from common import GlobalVariable
from exception import DefException
import socket
import logging
import time
from common import CommonDef

@CommonDef.singleton
class RpcClient:

    def __init__(self, NCPRev, lock):
        self.pool = GlobalVariable.BroachPool
        self.IntervalUdp = GlobalVariable.IntervalUdp # 重传间隔
        self.__NCPRev = NCPRev  # 响应NCP消息
        self.__NCPRevLock = lock

    @staticmethod
    def __send(data, ip, port):
        addr = (ip, port)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if len(data) > GlobalVariable.BufferLen :
            raise IOError("发送消息超过缓冲区3028字节长度限制")
        s.sendto(data, addr)
        logging.debug("发送消息 -> "+str(addr)+" 内容: "+data.decode("utf-8"))
        s.close()

    def sendCIM(self, msg, ip, port):
        data = MsgHandler.getCIM(msg)
        self.__send(data, ip, port)

    def sendNCP(self, msgId, isS, ip, port):
        data = MsgHandler.getNCP(msgId, isS)
        self.__send(data, ip, port)

    def sendNES(self, msgId, msg, ip, port):
        if self.__NCPRev.get(msgId) is not None:
            return "idRepeat"
        msgDict, msgInfoList = MsgHandler.getNES(msgId, GlobalVariable.params["params"]["rpcIp"],
                                                 GlobalVariable.params["params"]["rpcPort"], msg)
        for key in msgDict:
            self.__send(msgDict[key], ip, port)

        udpTimeOut = int(GlobalVariable.params["params"]["udpTimeOut"])
        timeUse = 0
        while timeUse <= udpTimeOut:
            revInfoList = self.__NCPRev.get(msgId)
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
                    with self.__NCPRevLock:
                        self.__NCPRev.pop(msgId)
                    return "idRepeat"
            if len(msgInfoList) == 0:
                break

            time.sleep(self.stepTime)
            timeUse = timeUse + self.stepTime

            revInfoList = self.__NCPRev.get(msgId)
            if revInfoList is None:
                continue
            for revInfo in revInfoList:
                msgInfo = revInfo[0]
                isS = revInfo[1]
                if isS == "0":
                    msgInfoList.remove(msgInfo)
                elif isS == "2":
                    #id重复 报错 重发
                    with self.__NCPRevLock:
                        self.__NCPRev.pop(msgId)
                    return "idRepeat"
            if len(msgInfoList) == 0:
                break

            for key in msgInfoList:
                self.__send(msgDict[key], ip, port)
        with self.__NCPRevLock:
            self.__NCPRev.pop(msgId)

        if timeUse > udpTimeOut:
            raise DefException.RpcSendNESTimeOutError("发送响应超时")

    def handlerNCP(self, msgId, msgInfo, isS):
        with self.__NCPRevLock:
            if self.__NCPRev.get(msgId) is None:
                msgInfoList = [[msgInfo, isS]]
                self.__NCPRev[msgId] = msgInfoList
            else:
                self.__NCPRev[msgId].append([msgInfo, isS])