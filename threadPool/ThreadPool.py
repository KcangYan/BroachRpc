import threading
import logging
import time
from exception.DefException import QueueOverflowError
LOG_FORMAT = '%(asctime)s -%(name)s- %(threadName)s-%(thread)d - %(levelname)s - %(message)s'
DATE_FORMAT = "%Y/%m/%d %H:%M:%S %p"
#日志配置
logging.basicConfig(level=logging.INFO,format=LOG_FORMAT,datefmt=DATE_FORMAT)

class CreatePool:
    def __init__(self, core=1, max=5, sleepTime=5, queue=None, poolName="pool", taskTimeOut=10):
        """
        :param core:  核心线程数
        :param max:  最大线程数
        :param sleepTime: 线程闲置回收时间
        :param queue: 队列对象
        :param poolName: 线程名
        :param taskTimeOut 任务执行返回值超时时间 即超过这个时间 异步返回值会提示timeout error
        """
        self.core = core
        self.max = max
        self.sleepTime = sleepTime
        self.queue = queue
        if queue == None:
            self.queue = ArrayQueue()
        if isinstance(queue, Queue) == False:
            raise Exception("请传入Queue类的实例对象")
        self.threadNum = 0
        self.poolName = poolName
        self.threadMap = {}
        self.threadMapLock = threading.RLock()
        self.taskTimeOut = taskTimeOut
        for i in range(0, self.core):
            self.__createThread(True)
        thread = threading.Thread(target=self.__aroundThreadFunc)
        thread.setName(self.poolName+"-检查线程")
        thread.start()
        logging.info("线程池 "+self.poolName+" 创建完成")

    def createThread(self):
        """
        供外部调用创建非核心线程
        :return: False 创建失败 True 创建成功
        """
        return self.__createThread()
    def __createThread(self, isCore=False):
        """
        内部使用创建线程
        :param isCore: 是否是核心线程
        :return:
        """
        with self.threadMapLock:
            if len(self.threadMap) >= self.max:
                return False
            thread = threading.Thread(target=self.__threadFunc)
            threadName = self.poolName + "-" + str(self.__getNum())
            thread.setName(threadName)
            condLock = threading.Condition()
            data = {"lock": condLock, "isCore": isCore, "time": time.time(), "isActive": True, "task": None}
            self.threadMap[threadName] = data
            thread.setDaemon(True)
            thread.start()
            return True

    def __aroundThreadFunc(self):
        if self.taskTimeOut > self.sleepTime:
            sleep = self.sleepTime
        else:
            sleep = self.taskTimeOut
        while True:
            time.sleep(sleep)
            try:
                for key in self.threadMap:
                    data = self.threadMap[key]
                    if data["isCore"] == False and data["task"] == None:
                        ex = time.time() - data["time"]
                        if ex > self.sleepTime:
                            # 关闭超时闲置非核心线程
                            with self.threadMapLock:
                                data["isActive"] = False
                                self.queue.notify(key, data["lock"])
                    if data["task"] is not None:
                        ex = time.time() - data["time"]
                        if ex > self.sleepTime:
                            data["task"]["return"] = "timeout error"
            except Exception:
                logging.exception(exc_info=True, msg="线程池异常")



    def __threadFunc(self):
        """
        线程执行函数 由isActive 属性控制线程是否结束
        :return:
        """
        threadName = threading.currentThread().getName()
        data = self.threadMap[threadName]
        while data.get("isActive"):
            logging.debug("正在尝试获取任务")
            task = self.queue.get(data["lock"], self)
            logging.debug("获取任务 "+str(task))
            data["task"] = task
            if task is None:
                continue
            try:
                task["return"] = task.get("func")(*task.get("args"), **task.get("kwargs"))
            except:
                task["return"] = "function handle Error"
                logging.exception("任务执行异常 " + str(task), exc_info=True)
            data["time"] = time.time()
            data["task"] = None
        with self.threadMapLock:
            self.threadMap.pop(threadName)
        logging.info(threadName+" 关闭")

    def __getNum(self):
        self.threadNum = self.threadNum + 1
        return self.threadNum

    def submit(self, fn, *args, **kwargs):
        """
        提交任务
        :param fn: 执行函数对象
        :param args: 参数
        :param kwargs: 参数
        :return: 异步对象dict
        """
        task = {"func": fn, "args": args, "kwargs": kwargs, "time": time.time(), "return": None}
        return self.queue.put(task, self)

class Queue:
    def put(self, task:dict, pool:CreatePool):
        raise Exception("请实现队列的PUT方法")
    def get(self, lock, pool:CreatePool):
        raise Exception("请实现队列的GET方法")
    def notify(self, threadName, lock):
        raise Exception("请实现队列的notify方法")

class ArrayQueue(Queue):
    def __init__(self, queueMax=5, isExcInfo=False, createThreadThreshold=None, queueFullWaitTime=1):
        """
        :param queueMax: 队列最大值
        :param isExcInfo: 溢出后是否报错 默认不报错交给主线程执行任务
        :param createThreadThreshold: 队列满足阈值后创建非核心线程
        :param queueFullWaitTime: 队列满了以后 等待任务接取时间
        """
        self.queueMax = queueMax
        self.queueList = []
        self.queueListLock = threading.RLock()
        self.threadMap = {}
        self.threadMapLock = threading.RLock()
        self.isExcInfo = isExcInfo
        self.createThreadThreshold = createThreadThreshold
        if createThreadThreshold == None:
            self.createThreadThreshold = queueMax
        self.queueFullWaitTime = queueFullWaitTime
    def put(self, task:dict, pool:CreatePool):
        """
        {"isActive": False, "func": fn, "args": args, "kwargs": kwargs, "time": time.time()}
        :return: 返回对象
         {'func': <function work at 0x00000262E39D6438>, 'args': (0,), 'kwargs': {}, 'time': 1661868095.0303512, 'return': 0}
        """
        queueLen = len(self.queueList)
        if queueLen >= self.createThreadThreshold:
            pool.createThread()
        if queueLen < self.queueMax:
            with self.queueListLock:
                self.queueList.append(task)
        if queueLen >= self.queueMax:
            isCreateThreadSuccess = pool.createThread()
            if isCreateThreadSuccess:
                with self.queueListLock:
                    self.queueList.append(task)
            else:
                time.sleep(self.queueFullWaitTime)
                if len(self.queueList) >= self.queueMax:
                    logging.error("任务队列已满，无法接取线程任务")
                    if self.isExcInfo:
                        raise QueueOverflowError("任务队列已满")
                    else:
                        logging.error("任务将交由主线程运行")
                        return task.get("func")(*task.get("args"), **task.get("kwargs"))
                else:
                    with self.queueListLock:
                        self.queueList.append(task)
        self.__discharged()
        return task

    def __discharged(self):
        """
        每次执行释放（唤醒）一个线程出来
        :return:
        """
        with self.threadMapLock:
            for key in self.threadMap:
                data = self.threadMap[key]
                if data["isActive"] == False:
                    lock = data["lock"]
                    lock.acquire()
                    lock.notify()
                    #lock.wait()
                    data["isActive"] = True
                    lock.release()
                    logging.debug("唤醒线程 "+key)
                    break

    def get(self, lock, pool:CreatePool):
        """
        data = {"thread": thread, "lock": condLock,
                "isActive": False, "isShutdown": False,
                "isCore": isCore, "time": time.time()}
        :return:
        """
        threadName = threading.currentThread().name
        while True:
            with self.queueListLock:
                queueLen = len(self.queueList)
                if queueLen > 0:
                    task = self.queueList[0]
                    self.queueList.remove(task)
                    return task
            data = {"lock": lock, "isActive": False}
            # 无任务时 阻塞线程 并将当前线程加入阻塞监听队列
            with self.threadMapLock:
                self.threadMap[threadName] = data
            lock.acquire()
            # lock.notify()
            lock.wait()
            lock.release()
            if threadName not in self.threadMap:
                break

    def notify(self, threadName, lock):
        """
        线程池关闭闲置线程
        :param threadName: 线程名
        :param lock: 锁
        :return:
        """
        logging.info("关闭线程: "+threadName)
        with self.threadMapLock:
            self.threadMap.pop(threadName)
        lock.acquire()
        lock.notify()
        # lock.wait()
        lock.release()

class SyncQueue(Queue):
    def __init__(self):
        self.threadMap = {}
        self.threadMapLock = threading.RLock()
        self.task = {}
        self.taskLock = threading.RLock()
        self.globalLockList = []
        self.globalLockListLock = threading.RLock()

    def get(self, lock, pool:CreatePool):
        threadName = threading.currentThread().name
        while True:
            if len(self.task) == 0:
                data = {"lock": lock, "isActive": False}
                # 无任务时 阻塞线程 并将当前线程加入阻塞监听队列
                with self.threadMapLock:
                    self.threadMap[threadName] = data
                lock.acquire()
                # lock.notify()
                lock.wait()
                lock.release()
                if threadName not in self.threadMap:
                    break
            else:
                with self.taskLock:
                    task = None
                    popKey = None
                    for key in self.task:
                        task = self.task[key]
                        popKey = key
                        break
                    self.task.pop(popKey)
                    lock = task["lock"]
                lock.acquire()
                lock.notify()
                # lock.wait()
                lock.release()
                return task

    def notify(self, threadName, lock):
        """
        线程池关闭闲置线程
        :param threadName: 线程名
        :param lock: 锁
        :return:
        """
        logging.info("关闭线程: "+threadName)
        with self.threadMapLock:
            self.threadMap.pop(threadName)
        lock.acquire()
        lock.notify()
        # lock.wait()
        lock.release()

    def __discharged(self, pool:CreatePool):
        """
        每次执行释放（唤醒）一个线程出来
        :return:
        """
        isDischarged = False
        with self.threadMapLock:
            for key in self.threadMap:
                data = self.threadMap[key]
                if data["isActive"] == False:
                    lock = data["lock"]
                    lock.acquire()
                    lock.notify()
                    #lock.wait()
                    data["isActive"] = True
                    lock.release()
                    logging.debug("唤醒线程 "+key)
                    isDischarged = True
                    break
        if isDischarged == False:
            pool.createThread()

    def put(self, task:dict, pool:CreatePool):
        logging.info(str(task))
        threadName = threading.currentThread().name
        lock = threading.Condition()
        task["lock"] = lock
        with self.taskLock:
            self.task[threadName] = task
        lock.acquire()
        #lock.notify()
        self.__discharged(pool)
        lock.wait()
        lock.release()
        return task

