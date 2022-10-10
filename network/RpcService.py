from common import CommonDef,GlobalVariable
from exception import DefException
from network import RpcServer,RpcClient
from apply import Component
import threading
import logging
import json
import time

"""
rpc 应用通信协议 json
{
  "funcId": "" , 远程调用函数id
  "args": "", 参数
  "kwargs": "", 参数
  "reqId": "0 18", 请求报文id 响应报文的话就是0
  "orgId": "0 18", 响应原报文id 请求报文的话就是0
  "status": "", 处理状态 200 成功 400 报错 404 找不到函数
  "result": "" 远程调用返回值
}
"""

@CommonDef.singleton
class RpcService:
    def __init__(self):
        self.rpcClient = RpcClient.RpcClient()
        self.rpcServer = RpcServer.RpcServer(self.rpcClient)
        self.rpcServer.addNESCallBack(self.__NESRevHandler)
        self.rpcServer.addCIMCallBack(self.__CIMRevHandler)
        self.__orgNES = {}
        self.__orgNESLock = threading.RLock()
    def serverStart(self):
        self.rpcServer.start()
        GlobalVariable.BroachPool.submit(self.__searchCluster)

    def sendRpc(self, ip: str, port: int, funcId, *args, **kwargs):
        #走底层通信NES消息 发送NES消息 对方应答NES消息
        reqId = CommonDef.getId(18)
        rpcTimeOut = int(GlobalVariable.params["rpcTimeOut"])
        with self.__orgNESLock:
            while self.__orgNES.__contains__(reqId):
                reqId = CommonDef.getId(18)
            lock = threading.Condition()
            self.__orgNES[reqId] = {"lock": lock, "result": DefException.CallRpcTimeOutError("响应超时")}
        reqJson = {"funcId": funcId, "args":args, "kwargs": kwargs, "reqId": reqId, "orgId":"0"}
        lock.acquire()
        self.__sendNES(json.dumps(reqJson, ensure_ascii=False), ip, port)
        lock.wait(rpcTimeOut)
        lock.release()

        result = self.__orgNES.get(reqId).get("result")
        with self.__orgNESLock:
            self.__orgNES.pop(reqId)
        if isinstance(result, DefException.CallRpcTimeOutError) is True:
            raise result
        else:
            status = result.get("status")
        if status == "400":
            raise DefException.RpcError(result.get("result"))
        elif status == "404":
            raise DefException.RpcFuncNotFundError(result.get("result"))
        else:
            return result.get("result")

    def __sendNES(self, reqJsonStr, ip, port):
        msgId = CommonDef.getId(18)
        sendResult = self.rpcClient.sendNES(msgId, reqJsonStr, ip, port)
        while sendResult == "idRepeat":
            logging.error("NES通信消息id，重复异常。重新随机id")
            msgId = CommonDef.getId(18)
            sendResult = self.rpcClient.sendNES(msgId, reqJsonStr, ip, port)

    def __searchCluster(self):
        addressList = GlobalVariable.params.get("clusterAddress")
        localIp = GlobalVariable.params.get("rpcIp")
        localPort = GlobalVariable.params.get("rpcIp")
        for address in addressList:
            ip = address.split(":")[0]
            port = address.split(":")[1]
            msg = localIp+":"+localPort
            self.rpcClient.sendCIM(msg, ip, port)
        while True:
            logging.debug("启动集群活动探测线程")
            time.sleep(2)


    def __CIMRevHandler(self, msg):
        logging.debug("收到CIM消息: "+ msg)
        ip = msg.split(":")[0]
        port = msg.split(":")[1]
        self.sendRpc(ip, port, "getRpcRoute")


    def __NESRevHandler(self, msg, revIp, revPort):
        try:
            revJson = json.loads(msg)
        except Exception as e:
            logging.exception(exc_info=True, msg="json 解析异常 "+str(e))
            return
        logging.debug("接收到NES消息: "+ msg)
        orgId = revJson.get("orgId")
        if str(orgId) != "0":
            #响应回调 结束阻塞
            if self.__orgNES.get(orgId) is not None:
                with self.__orgNESLock:
                    self.__orgNES.get(orgId)["result"] = revJson
                lock = self.__orgNES.get(orgId).get("lock")
                lock.acquire()
                lock.notify()
                lock.release()
        else:
            reqId = revJson.get("reqId")
            funcId = revJson.get("funcId")
            fn = GlobalVariable.FuncRoute.get(funcId)
            if fn is None:
                re = {"status": "404", "result": "funcNotFund", "orgId": reqId}
                self.__sendNES(json.dumps(re), revIp, revPort)
            else:
                args = revJson.get("args")
                kwargs = revJson.get("kwargs")
                try:
                    result = fn(*args, **kwargs)
                    status = "200"
                except Exception as e:
                    result = str(e)
                    status = "400"
                re = {"status": status, "result": result, "orgId": reqId}
                self.__sendNES(json.dumps(re), revIp, revPort)


instance = None
