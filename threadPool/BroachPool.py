import threading
import logging
import time
from exception.DefException import QueueOverflowError, ThreadPoolIsShutdown
LOG_FORMAT = '%(asctime)s -%(name)s- %(threadName)s-%(thread)d - %(levelname)s - %(message)s'
DATE_FORMAT = "%Y/%m/%d %H:%M:%S %p"
#日志配置
logging.basicConfig(level=logging.DEBUG,format=LOG_FORMAT,datefmt=DATE_FORMAT)

class Pool:
    def __init__(self, core=1, threadMax=5, keepAliveTime=6, queue=None, poolName="pool", taskTimeOut=10):
        """
        :param core:  核心线程数
        :param max:  最大线程数
        :param sleepTime: 线程闲置回收时间
        :param queue: 队列对象
        :param poolName: 线程名
        :param taskTimeOut 任务执行返回值超时时间 即超过这个时间 异步返回值会提示timeout error
        """
        self.core = core
        self.threadMax = threadMax
        self.keepAliveTime = keepAliveTime
        self.queue = queue
        if queue is None:
            self.queue = ArrayQueue()
        if isinstance(queue, Queue) is False:
            raise Exception("请传入Queue类的实例对象")
        self.threadNum = 0
        self.poolLock = threading.RLock()
        self.poolName = poolName
        self.taskTimeOut = taskTimeOut
        self.poolStatus = True
        for i in range(0, self.core):
            self.createThread(True)
        logging.debug("线程池 "+self.poolName+" 创建完成")

    def createThread(self, isCore=False):
        """
        创建线程 false标识创建失败
        :param isCore: 是否核心线程
        :return: 成功或者失败
        """
        with self.poolLock:
            if self.threadNum >= self.threadMax:
                return False
            else:
                thread = threading.Thread(target=self.__threadFunc, kwargs={"isCore": isCore})
                threadName = self.poolName + "-" + str(self.threadNum + 1)
                thread.setName(threadName)
                self.threadNum = self.threadNum + 1
                thread.start()
                return True

    def __threadFunc(self, isCore):
        """
        工作线程执行函数
        会像队列的get方法获取任务，None标识退出线程
        或者poolStatus = false 退出循环结束工作线程
        :param isCore: 是否核心线程
        :return: void
        """
        data = {"isCore": isCore, "lock": threading.Condition(), "isWork": False}
        while self.poolStatus:
            task = self.queue.get(data, self)
            if task is None:
                break
            data["isWork"] = True
            try:
                task["return"] = task.get("func")(*task.get("args"), **task.get("kwargs"))
            except Exception as e:
                task["return"] = "taskError: "+str(e)
                logging.exception("任务执行异常 " + str(task), exc_info=True)
            data["isWork"] = False
        logging.debug("exit")
        with self.poolLock:
            self.threadNum = self.threadNum - 1

    def submit(self, fn, *args, **kwargs):
        """
        提交任务
        {"func": fn, "args": args, "kwargs": kwargs, "return": None}
        :param fn: 执行函数对象
        :param args: 参数
        :param kwargs: 参数
        :return: 异步对象dict
        """
        if self.poolStatus:
            task = {"func": fn, "args": args, "kwargs": kwargs, "return": None}
            return self.queue.put(task, self)
        else:
            raise ThreadPoolIsShutdown("线程池已关闭，无法提交任务")

    def shutDown(self):
        """
        关闭线程池
        :return:
        """
        self.poolStatus = False

class Queue:
    def put(self, task:dict, pool:Pool):
        """
        线程池调用put方法提交任务
        :param task: {"func": fn, "args": args, "kwargs": kwargs, "return": None}
        :param pool: 线程池对象
        :return: {"func": fn, "args": args, "kwargs": kwargs, "return": None}
        """
        raise Exception("请实现队列的PUT方法")
    def get(self, thread:dict, pool:Pool):
        """
        线程池调取get方法获取任务
        :param thread: {"isCore": isCore, "lock": threading.Condition(), "isWork": False}
        :param pool: 线程池对象
        :return: void
        """
        raise Exception("请实现队列的GET方法")

class ArrayQueue(Queue):
    def __init__(self, queueMax=5, isExcInfo=False, createThreadThreshold=None):
        """
        :param queueMax: 队列最大值
        :param isExcInfo: 溢出后是否报错 默认不报错交给提交任务的线程执行任务
        :param createThreadThreshold: 队列满足阈值后创建非核心线程
        :param queueFullWaitTime: 队列满了以后 等待任务接取时间
        """
        self.queueMax = queueMax
        self.queueList = []
        self.queueListLock = threading.RLock()
        self.threadList = []
        self.threadListLock = threading.RLock()
        self.isExcInfo = isExcInfo
        self.createThreadThreshold = createThreadThreshold
        if createThreadThreshold is None:
            self.createThreadThreshold = queueMax

    def put(self, task:dict, pool:Pool):
        """
        当提交任务到线程池时 线程池会调用队列的put方法传递任务对象处理 并将put方法的返回值作为异步对象返回给提交任务的线程
        队列满了以后 根据设置 是否抛出异常 中断线程
        :param task: {"func": fn, "args": args, "kwargs": kwargs, "return": None}
        :param pool: 调用的线程池对象
        :return: {"func": fn, "args": args, "kwargs": kwargs, "return": wait} dict 待任务执行完成后 return键值将会获得返回对象
        """
        if len(self.queueList) >= self.queueMax and pool.threadNum == pool.threadMax:
            if self.isExcInfo:
                raise QueueOverflowError("任务队列已满")
            else:
                logging.error("任务队列已满，将交由提交线程执行任务")
                try:
                    task["return"] = task.get("func")(*task.get("args"), **task.get("kwargs"))
                    return task
                except Exception as e:
                    task["return"] = "taskError: "+str(e)
                    logging.exception("任务执行异常 " + str(task), exc_info=True)

        with self.queueListLock:
            self.queueList.append(task)

        if len(self.queueList) >= self.createThreadThreshold:
            pool.createThread()

        for thread in self.threadList:
            if thread["isWork"] is False:
                lock = thread["lock"]
                lock.acquire()
                lock.notify()
                lock.release()
        return task

    def get(self, thread:dict, pool:Pool):
        """
        工作线程获取任务 调用get方法 从队列中获取任务
        没有获取到任务 就用锁阻塞线程 等待唤醒获取任务
        当非核心线程闲置时间超过阈值时 返回None 结束工作线程
        :param thread: 线程对象 {"isCore": isCore, "lock": threading.Condition(), "isWork": False}
        :param pool: 线程池对象
        :return:
        """
        if thread not in self.threadList:
            with self.threadListLock:
                self.threadList.append(thread)

        while True:
            task = None
            with self.queueListLock:
                if len(self.queueList) > 0:
                    task = self.queueList[0]
                    self.queueList.remove(task)
            if task is not None:
                return task
            else:
                sTime = time.time()
                lock = thread["lock"]
                lock.acquire()
                lock.wait(pool.keepAliveTime)
                lock.release()
                eTime = time.time()
                if thread["isCore"] == False and (eTime - sTime) >= pool.keepAliveTime:
                    with self.threadListLock:
                        self.threadList.remove(thread)
                    return None
                if pool.poolStatus == False and len(self.queueList) == 0:
                    return None

class SyncQueue(Queue):
    def __init__(self):
        self.threadList = []
        self.threadListLock = threading.RLock()
        self.task = {}
        self.taskLock = threading.RLock()
        self.waitTask = []
        self.waitTaskLock = threading.RLock()

    def put(self, task:dict, pool:Pool):
        """
        阻塞提交任务的线程 直到提交的任务被线程获取执行
        :param task: 任务对象 {"isCore": isCore, "lock": threading.Condition(), "isWork": False}
        :param pool: 线程池对象
        :return:
        """
        putLock = threading.Condition()

        idleThread = None
        with self.threadListLock:
            for thread in self.threadList:
                if thread["isWork"] is False:
                    idleThread = thread
                    thread["isWork"] = True
        if idleThread is None:
            putLock.acquire()
            data = {"putLock": putLock, "task": task}
            with self.waitTaskLock:
                self.waitTask.append(data)
            pool.createThread()
            putLock.wait()
            putLock.release()
        else:
            with self.taskLock:
                self.task[idleThread["lock"]] = task
            lock = idleThread["lock"]
            lock.acquire()
            lock.notify()
            lock.release()
        return task

    def get(self, thread:dict, pool:Pool):
        """
        没有获取到任务就阻塞 获取到任务就把原本阻塞提交任务线程的锁释放掉
        :param thread: 线程对象
        :param pool: 线程池对象
        :return:
        """
        lock = thread["lock"]
        if thread not in self.threadList:
            with self.threadListLock:
                self.threadList.append(thread)
                self.task[lock] = None
        while True:
            with self.taskLock:
                task = self.task[lock]
                self.task[lock] = None
            if task is not None:
                return task
            else:
                if len(self.waitTask) != 0:
                    with self.waitTaskLock:
                        data = self.waitTask[0]
                        self.waitTask.remove(data)
                    putLock = data["putLock"]
                    task = data["task"]
                    putLock.acquire()
                    putLock.notify()
                    putLock.release()
                    return task
                sTime = time.time()
                lock.acquire()
                lock.wait(pool.keepAliveTime)
                lock.release()
                eTime = time.time()
                if thread["isCore"] == False and (eTime - sTime) >= pool.keepAliveTime:
                    with self.threadListLock:
                        self.threadList.remove(thread)
                    return None
                if pool.poolStatus is False and self.task is None:
                    return None

SyncPool = Pool(core=1, threadMax=5, keepAliveTime=6, queue=SyncQueue(), poolName="SyncPool")
ArrayPool = Pool(core=1, threadMax=5, keepAliveTime=6,
                 queue=ArrayQueue(queueMax=100, isExcInfo=False, createThreadThreshold=5), poolName="ArrayPool")