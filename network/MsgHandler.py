import threading
from exception.DefException import ReceiveBuffOverError
from common import GlobalVariable
import time
"""
定义消息 
 消息类型3位 
 NES 消息 - 双向应答
 消息id  报文Id（18位） + 消息序号 00000 + 00000 10位 前五位表示总消息数量 后五位表示当前消息序号
 接收响应消息地址 15位ip地址 5位端口号 127.  0.  0.  118080 -> 127.0.0.1 18080
 固定字节共 3 + 18 + 5 + 5 + 15 + 5 = 51 位
 报文长度 = 3028 - 51 = 2977
 NCP 消息 - 响应NES消息
 消息id  发送方id 28位
 处理结果 1位 0 成功 1 失败 2 消息id当前已存在
 CIM 消息 
 缓冲区字节以内的单向udp消息
"""

def decodeData(data):
    msgType = data[0:3]
    msg = data[3:len(data)]
    return msgType.decode("utf-8"), msg

def getCIM(msg):
    data = "CIM" + msg
    data = data.encode("utf-8")
    if len(data) > GlobalVariable.BufferLen:
        raise ReceiveBuffOverError("CIM 消息不能超过 3025字节")
    return data

def decodeCIM(data):
    return data.decode("utf-8")

def getNCP(msgIdInfo, isS="0"):
    data = "NCP" + msgIdInfo + isS
    data = data.encode("utf-8")
    return data

def decodeNCP(data):
    msgId = data[0:18]
    msgInfo = data[18:28]
    isS = data[28:29]
    return msgId.decode("utf-8"), msgInfo.decode("utf-8") ,isS.decode("utf-8")

def getNES(msgId, revIp, revPort ,msg):
    msgDict = {}
    msgInfoList = []
    msgData = msg.encode("utf-8")
    msgLenLimit = GlobalVariable.BufferLen-51
    msgLen = len(msgData)
    if msgLen > msgLenLimit:
        y = msgLen%msgLenLimit
        if y == 0:
            order = int(msgLen/msgLenLimit)
        else:
            order = int(msgLen/msgLenLimit) + 1
        revAddress = getIpPortStr(revIp, revPort)
        orderS = getCover(str(order), 5, "0")
        for i in range(0, order):
            data = "NES" + msgId + orderS + getCover(str(i), 5, "0") + revAddress
            msgInfoList.append(orderS + getCover(str(i), 5, "0"))
            data = data.encode("utf-8")
            start = i*msgLenLimit
            end = (i+1) * msgLenLimit
            if end > msgLen:
                end = msgLen
            msgDict[orderS + getCover(str(i), 5, "0")] = data+msgData[start:end]
    else:
        data = "NES" + msgId + "00001" + "00000" + getIpPortStr(revIp, revPort)
        data = data.encode("utf-8")
        msgDict["00001" + "00000"] = data+msgData
        msgInfoList.append("00001" + "00000")
    return msgDict, msgInfoList

def decodeNES(data):
    msgId = data[0:18]
    msgInfo = data[18:28]
    revIp = data[28:43].decode("utf-8")
    revPort = data[43:48].decode("utf-8")
    msgPart = data[48:]
    return msgId.decode("utf-8"), msgInfo.decode("utf-8"), revIp.replace(" ",""), int(revPort), msgPart

def getIpPortStr(ip:str, port):
    ipl = ip.split(".")
    ips = ""
    for item in ipl:
        ips = ips + getCover(item, 3, " ") + "."
    ips = ips[0:15]
    return ips + getCover(str(port), 5, "0")

def getCover(s, l:int, coverStr):
    ls = len(s)
    lx = l - ls
    if lx <= 0:
        return s
    else:
        re = s
        for i in range(0, lx):
            re = coverStr+re
        return re
