import json
import logging
from network import RpcClient, RpcHandler
from config import GlobalVariable
from exception import DefException

"""
rpc 应用通信协议 json
request
{
  "funcId": "" ,
  "args": "",
  "kwargs": ""
}
response
{
   "status": "",
   "return": ""
}
"""


def callRpc(reqJson: dict, ip: str, port: int):
    reqJsonStr = json.dumps(reqJson)
    msgId = RpcHandler.getId(18)
    sendResult = RpcClient.Client.sendNES(msgId, reqJsonStr, ip, port)
    while sendResult == "idRepeat":
        logging.error("NES通信消息id，重复异常。重新随机id")
        msgId = RpcHandler.getId(18)
        sendResult = RpcClient.Client.sendNES(msgId, reqJsonStr, ip, port)
    getResult = RpcHandler.getNESRev(msgId)
    if getResult == "timeOut":
        raise DefException.CallRpcTimeOutError("rpc call back error")
    if getResult is not None:
        return json.loads(getResult)
    else:
        return None

def callBackNES(reqJson: str, msgId: str, ip: str, port: int):
    logging.debug("收到NES消息" + msgId + ": " + reqJson)
    req = json.loads(reqJson)
    funcId = req.get("funcId")
    fn = GlobalVariable.FuncRoute.get(funcId)
    if fn is None:
        result = req.get("return")
        if result is not None:
            pass
        else:
            re = {"status": "404", "return": "funcNotFund"}
            re = json.dumps(re)
            sendResult = RpcClient.Client.sendNES(msgId, re, ip, port)
    else:
        args = req.get("args")
        kwargs = req.get("kwargs")
        try:
            if args is not None and kwargs is not None:
                result = fn(*args, **kwargs)
            elif args is not None and kwargs is None:
                result = fn(*args)
            elif args is None and kwargs is not None:
                result = fn(**kwargs)
            else:
                result = fn()
        except Exception as e:
            result = str(e)
        re = {"status": "200", "return": result}
        re = json.dumps(re)
        sendResult = RpcClient.Client.sendNES(msgId, re, ip, port)
