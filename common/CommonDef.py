import random
import threading
import time
import logging
from common import GlobalVariable

"""
单例装饰器
"""
def singleton(cls):
    """
    单例装饰器
    :param cls: 类
    :return: 实例
    """
    _instance_dict = {}  # 采用字典，可以装饰多个类，控制多个类实现单例模式
    lock = threading.RLock()
    def inner(*args, **kwargs):
        if cls in _instance_dict:
            return _instance_dict.get(cls)
        with lock:
            if cls not in _instance_dict:
                _instance_dict[cls] = cls(*args, **kwargs)
            return _instance_dict.get(cls)
    return inner

"""
id获取
"""
def getId(n=9):
    """
    生成随机id 默认9位
    :param n: 位数
    :return: 字符串id
    """
    id = ""
    template = "0987654321qwertyuioplkjhgfdsazxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
    for i in range(0,n):
        strIndex = random.randint(0,61)
        id = id + template[strIndex]
    return id

"""
定时任务执行函数
"""
def timerTask(tasks:list):
    while True:
        time.sleep(1)
        for item in tasks:
            fn = item.get("fn")
            timeStep = int(item.get("timeStep"))
            lastTime = item.get("time")
            if lastTime is None:
                item["time"] = time.time()
                fn()
            else:
                ex = time.time() - lastTime
                if ex >= timeStep:
                    item["time"] = time.time()
                    fn()

"""
rpc装饰器 获取程序启动时的函数路由表 和 BroachFramework包里的一样
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