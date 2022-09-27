from network import MsgHandler
from common import GlobalVariable
from exception import DefException
import socket
import logging
import time
import threading
from common import CommonDef

@CommonDef.singleton
class RpcClient:

    def __init__(self):
        self.pool = GlobalVariable.BroachPool
        self.IntervalUdp = GlobalVariable.IntervalUdp # 重传间隔
        self.__NCPRev = {}  # 响应NCP消息
        self.__NCPRevLock = threading.RLock()

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

    def sendNCP(self, msgIdInfo, isS, ip, port):
        data = MsgHandler.getNCP(msgIdInfo, isS)
        self.__send(data, ip, port)

    def sendNES(self, msgId, msg, ip, port):
        if self.__NCPRev.get(msgId) is not None:
            return "idRepeat"
        msgDict, msgInfoList = MsgHandler.getNES(msgId, GlobalVariable.params["rpcIp"],
                                                 GlobalVariable.params["rpcPort"], msg)

        udpTimeOut = int(GlobalVariable.params["udpTimeOut"])
        timeUse = 0
        lock = threading.Condition()
        with self.__NCPRevLock:
            self.__NCPRev[msgId] = {"lock": lock, "msgInfo": None}

        while timeUse <= udpTimeOut:
            #time.sleep(GlobalVariable.IntervalUdp)
            lock.acquire()
            if timeUse == 0:
                for key in msgInfoList:
                    self.__send(msgDict[key], ip, port)
            lock.wait(GlobalVariable.IntervalUdp)
            lock.release()
            timeUse = timeUse + GlobalVariable.IntervalUdp
            revInfoList = self.__NCPRev.get(msgId).get("msgInfo")
            if revInfoList is not None:
                for revInfo in revInfoList:
                    msgInfo = revInfo[0]
                    isS = revInfo[1]
                    if isS == "0" and msgInfo in msgInfoList:
                        msgInfoList.remove(msgInfo)
                    elif isS == "2":#id重复 报错 重发
                        with self.__NCPRevLock:
                            self.__NCPRev.pop(msgId)
                        return "idRepeat"
            if len(msgInfoList) == 0:
                break

        with self.__NCPRevLock:
            self.__NCPRev.pop(msgId)
        if timeUse > udpTimeOut and len(msgInfoList) != 0:
            raise DefException.RpcSendNESTimeOutError("发送响应超时 ->"+ip+":"+str(port)+" 无应答")

    def handlerNCP(self, msgId, msgInfo, isS):
        with self.__NCPRevLock:
            if self.__NCPRev.get(msgId) is None:
                return
            lock = self.__NCPRev.get(msgId).get("lock")
            if self.__NCPRev.get(msgId).get("msgInfo") is None:
                msgInfoList = [[msgInfo, isS]]
                self.__NCPRev.get(msgId)["msgInfo"] = msgInfoList
            else:
                self.__NCPRev.get(msgId)["msgInfo"].append([msgInfo, isS])
        lock.acquire()
        lock.notify()
        lock.release()