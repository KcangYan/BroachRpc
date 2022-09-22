import random
import threading

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

