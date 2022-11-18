from common import GlobalVariable
from exception import DefException
import logging
import copy
from network import RpcService

"""
rpc装饰器 获取程序启动时的函数路由表
"""
def rpcRoute(name=None):
    def getFun(fn):
        if name is None:
            routeName = fn.__name__
        else:
            routeName = name
        if GlobalVariable.FuncRoute.get(routeName) is None:
            GlobalVariable.FuncRoute[routeName] = fn
            logging.debug("function: "+routeName+" registry route success")
        else:
            logging.error(routeName+" registry route fail，name is replace")
        return fn
    return getFun

"""
rpc装饰器 调用rpc服务
"""
def rpcCall(name=None):
    def getFun(fn):
        def getParams(*args, **kwargs):
            if name is None:
                routeName = fn.__name__
            else:
                routeName = name
            if routeName in GlobalVariable.FuncRoute.keys():
                logging.info("调用内部函数 -> "+routeName)
                rpcFn = GlobalVariable.FuncRoute.get(routeName)
                return rpcFn(*args, **kwargs)
            else:
                if routeName in GlobalVariable.FuncRouteRpc.keys():
                    rpcFnInfo = GlobalVariable.FuncRouteRpc.get(routeName)
                    if rpcFnInfo is not None:
                        ipList = rpcFnInfo.keys()
                        reqAddress = ""
                        minReqNum = 100
                        for address in ipList:
                            info = rpcFnInfo.get(address)
                            reqNum = info.get("reqNum")
                            if reqNum >= 100:
                                info["reqNum"] = 0
                                reqAddress = address
                                break
                            if reqNum < minReqNum:
                                minReqNum = reqNum
                                reqAddress = address
                        if reqAddress == "":
                            raise DefException.RpcFuncNotFundError(routeName+" 没有可用的服务端")
                        rpcFnInfo[reqAddress]["reqNum"] = minReqNum + 1
                        ip = reqAddress.split(":")[0]
                        port = reqAddress.split(":")[1]
                        return RpcService.instance.sendRpc(ip,port,routeName, *args, **kwargs)
                    else:
                        raise DefException.RpcFuncNotFundError(routeName+" is not Fund")
                else:
                    raise DefException.RpcFuncNotFundError(routeName+" is not Fund")
            #logging.debug("rpc调用"+routeName)
            #re = RpcService.RpcService.sendRpc(routeName, )
            #logging.debug("rpc调用结束 结果:"+re)
            #return re
        return getParams
    return getFun