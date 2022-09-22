import json
import logging
import threading
from network import RpcClient, RpcHandler
from config import GlobalVariable
from exception import DefException

"""
rpc 应用通信协议 json
{
  "funcId": "" , 远程调用函数id
  "args": "", 参数
  "kwargs": "", 参数
  "reqId": "0 18", 请求报文id
  "orgId": "0 18", 响应原报文id 无的话就是0
  "status": "", 处理状态
  "return": "" 远程调用返回值
}
"""
OrgReqNES = {}
OrgReqNESLock = threading.RLock()

def callRpc(reqJson: dict, ip: str, port: int):
    reqJsonStr = json.dumps(reqJson)
    reqId = reqJson.get("reqId")
    lock = threading.Condition()
    with OrgReqNESLock:
        OrgReqNES[reqId] = {"lock": lock, "return": DefException.CallRpcTimeOutError("响应超时")}
    rpcTimeOut = int(GlobalVariable.params["params"]["rpcTimeOut"])
    lock.acquire()
    sendNES(reqJsonStr, ip, port)
    lock.wait(rpcTimeOut)
    lock.release()

    re = OrgReqNES.get(reqJson.get("reqId")).get("return")
    with OrgReqNESLock:
        OrgReqNES.pop(reqId)
    if isinstance(re, DefException.CallRpcTimeOutError) is True:
        raise re
    else:
        status = re.get("status")
        if status == "400":
            raise DefException.RpcError(re.get("return"))
        elif status == "404":
            raise DefException.RpcFuncNotFundError(re.get("return"))
        else:
            return re.get("return")


def sendNES(reqJsonStr, ip, port):
    msgId = RpcHandler.getId(18)
    sendResult = RpcClient.Client.sendNES(msgId, reqJsonStr, ip, port)
    while sendResult == "idRepeat":
        logging.error("NES通信消息id，重复异常。重新随机id")
        msgId = RpcHandler.getId(18)
        sendResult = RpcClient.Client.sendNES(msgId, reqJsonStr, ip, port)

def callBackNES(reqJson: str, ip: str, port: int):
    logging.debug("收到NES消息: " + reqJson)
    try:
        req = json.loads(reqJson)
    except Exception as e:
        logging.exception(exc_info=True, msg="消息JSON序列化异常 "+str(e))
        return
    orgId = req.get("orgId")
    if orgId == "0":
        #请求
        reqId = req.get("reqId")
        funcId = req.get("funcId")
        fn = GlobalVariable.FuncRoute.get(funcId)
        if fn is None:
            re = {"status": "404", "return": "funcNotFund", "orgId": reqId}
            sendNES(json.dumps(re), ip, port)
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
                status = "200"
            except Exception as e:
                result = str(e)
                status = "400"
            re = {"status": status, "return": result, "orgId": reqId}
            sendNES(json.dumps(re), ip, port)
    elif len(orgId) == 18:
        #响应
        if OrgReqNES.get(orgId) is not None:
            with OrgReqNESLock:
                OrgReqNES.get(orgId)["return"] = req
            lock = OrgReqNES.get(orgId).get("lock")
            lock.acquire()
            lock.notify()
            lock.release()


