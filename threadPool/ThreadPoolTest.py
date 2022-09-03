import threading
import logging
import time
LOG_FORMAT = '%(asctime)s -%(name)s- %(threadName)s-%(thread)d - %(levelname)s - %(message)s'
DATE_FORMAT = "%Y/%m/%d %H:%M:%S %p"
#日志配置
logging.basicConfig(level=logging.INFO,format=LOG_FORMAT,datefmt=DATE_FORMAT)

class CreatePool:
    def __init__(self, core=1, max=5, queueMax=None):
        self.core = core
        self.max = max
        if queueMax==None:
            self.queueMax = 5
        else:
            self.queueMax = queueMax
        self.queueLock = threading.RLock()
        self.threadPoolLock = threading.RLock()
        self.queue = []
        self.threadPool = {}
        for i in range(0, core):
            self.__createThread(True)
        logging.info("线程池启动成功！")

    def __threadFunc(self):
        """
        线程任务 无任务或者任务运行结束时 挂起等待
        :return:
        """
        logging.info(threading.currentThread().name + "启动成功")
        data = self.threadPool.get(threading.currentThread().name)
        lock = data.get("lock")
        lock.acquire()
        while data.get("isShutdown") != True :
            threadTask = self.__getTask()
            logging.info(str(threadTask))
            #取队列未被执行的任务 执行
            if threadTask != None:
                with self.threadPoolLock:
                    data["isActive"] = True
                try:
                    threadTask.get("func")(*threadTask.get("args"), **threadTask.get("kwargs"))
                except:
                    logging.exception("任务执行异常 "+str(threadTask),exc_info=True)
                with self.queueLock:
                    self.queue.remove(threadTask)
                with self.threadPoolLock:
                    data["isActive"] = False
            else:
                lock.wait()
        logging.info("线程结束")
        lock.release()

    def __getTask(self):
        """
        获取队列任务
        :return: None 即无可运行任务 否则返回任务map
        """
        # 取队列未被执行的任务 执行
        with self.queueLock:
            for task in self.queue:
                if task.get("isActive") == False:
                    task["isActive"] = True
                    return task

    def __queueAdd(self, task:dict):
        """
        判断队列是否已满 满了就报错
        没满就加进去 调用线程去处理
        :param task: 任务
        :return: 无返回
        """
        with self.queueLock:
            queueLen = len(self.queue)
            if queueLen >= self.queueMax:
                threadNum = len(self.threadPool)
                if threadNum < self.max:
                    self.queue.append(task)
                else:
                    raise Exception("队列溢出")
            else:
                self.queue.append(task)
        #离开队列锁
        if queueLen >= self.queueMax:
            self.__createThread(False)
        self.__controlThread()

    def __controlThread(self):
        """
        启动闲置线程去获取任务处理
        :return:
        """
        with self.threadPoolLock:
            for threadName in self.threadPool:
                data = self.threadPool.get(threadName)
                isActive = data.get("isActive")
                if isActive == False:
                    lock = data.get("lock")
                    lock.acquire()
                    lock.notify()
                    lock.release()

    def __createThread(self, isCore):
        """
        创建线程
        :return:
        """
        condLock = threading.Condition()
        thread = threading.Thread(target=self.__threadFunc)
        data = {"thread": thread, "lock": condLock,
                "isActive": False, "isShutdown": False,
                "isCore": isCore, "time": time.time()}
        with self.threadPoolLock:
            self.threadPool[thread.getName()] = data
        thread.start()

    def __IdleThread(self):
        queueLen = len(self.queue)
        threadNum = len(self.threadPool)
        if queueLen == 0 and threadNum > self.core:
            with self.threadPoolLock:
                delThreadList = []
                for threadName in self.threadPool:
                    data = self.threadPool.get(threadName)
                    isActive = data.get("isActive")
                    if isActive == False :
                        data["isShutdown"] = True
                        lock = data.get("lock")
                        lock.acquire()
                        lock.notify()
                        lock.release()
                        delThreadList.append(threadName)
                        item = item + 1
                for name in delThreadList:
                    del self.threadPool[name]

    def submit(self, fn, *args, **kwargs):
        """
        提交任务
        :param fn: 任务函数
        :return: 无返回
        """
        task = {"isActive": False, "func": fn, "args": args, "kwargs": kwargs, "time": time.time()}
        try:
            self.__queueAdd(task)
        except Exception:
            logging.exception("队列异常, 任务将交由主线程处理", exc_info=True)
            fn(*args, **kwargs)


task = {"a":1, "b":2}
v = task.keys()
for key in v:
    print(key)