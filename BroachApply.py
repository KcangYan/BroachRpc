from common import GlobalVariable
import logging

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
            logging.debug("rpc调用"+routeName)
            #re = RpcService.RpcService.sendRpc(routeName, )
            #logging.debug("rpc调用结束 结果:"+re)
            #return re
        return getParams
    return getFun