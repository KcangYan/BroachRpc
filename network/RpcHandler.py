import socket
import random
import time
from exception.DefException import ReceiveBuffOverError
from threadPool.ThreadPool import *
"""
定义消息 
 交互id (9位) 基于每个通信客户端生成 （每次程序启动会生成一个id 用于接下来的交互）
 消息类型3位 
 NES 消息 - 双向应答
 消息id  报文Id（9位） + 消息序号 00000 + 00000 10位 前五位表示总消息数量 后五位表示当前消息序号
 接收响应消息地址 15位ip地址 5位端口号 127.  0.  0.  118080 -> 127.0.0.1 18080
 NCP 消息 - 响应NES消息
 消息id  发送方id 19位
 处理结果 1位 0 成功 1 失败 2 消息id当前已存在
 CIM 消息 
 缓冲区字节以内的单向udp消息
"""
NESServer = {}
NESClient = {}

def decodeData(data):
    clientId = data[0:9]
    msgType = data[9:12]
    msg = data[12:len(data)]
    return clientId.decode("utf-8"), msgType.decode("utf-8"), msg

def getId(n=9):
    id = ""
    template = "0987654321qwertyuioplkjhgfdsazxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
    for i in range(0,n):
        strIndex = random.randint(0,61)
        id = id + template[strIndex]
    return id.encode("utf-8")

def getCIM(clientId, msg):
    data = clientId + "CIM" + msg
    data = data.encode("utf-8")
    if len(data) > 1024:
        raise ReceiveBuffOverError("CIM 消息不能超过 1015字节")
    return data

def decodeCIM(data):
    return data.decode("utf-8")

def getNCP(clientId, msgId, isS="0"):
    data = clientId + "NCP" + msgId + isS
    data = data.encode("utf-8")
    return data

def decodeNCP(data):
    msgId = data[0:19]
    isS = data[19:20]
    return msgId.decode("utf-8"), isS.decode("utf-8")
