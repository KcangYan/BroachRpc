import threading
#单例装饰器
def singleton(cls):
    _instance_dict = {}  # 采用字典，可以装饰多个类，控制多个类实现单例模式
    lock = threading.RLock()
    print("sign")
    def inner(*args, **kwargs):
        with lock:
            if cls not in _instance_dict:
                _instance_dict[cls] = cls(*args, **kwargs)
            return _instance_dict.get(cls)
    return inner