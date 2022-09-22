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
            logging.debug(routeName+" __init__ registry route success")
        else:
            logging.error(routeName+" registry route fail，name is replace")
        return fn
    return getFun


