import json
import logging
from network import RpcClient,RpcHandler

def callRpc(reqJson:dict, ip:str, port:int):
    reqJsonStr = json.dumps(reqJson)
    msgId = RpcHandler.getId(18)
    sendResult = RpcClient.Client.sendNES(msgId, reqJsonStr, ip, port)
    while sendResult == "idRepeat":
        logging.error("NES通信消息id，重复异常。重新随机id")
        msgId = RpcHandler.getId(9)
        sendResult = RpcClient.Client.sendNES(msgId, reqJsonStr, ip, port)
    getResult = RpcHandler.getNESRev(msgId)
    if getResult is not None:
        return json.loads(getResult)
    else:
        return None
