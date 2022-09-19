from network import RpcServer, RpcClient
from threadPool import BroachPool
from config import GlobalVariable
import json
import logging

"""
框架主启动入口
"""
def run(path='./application.json'):
    # 初始化配置
    getConfig(path)
    # 初始化日志配置
    LOG_FORMAT = '%(asctime)s -%(name)s- %(threadName)s-%(thread)d - %(levelname)s - %(message)s'
    DATE_FORMAT = "%Y/%m/%d %H:%M:%S %p"
    logLevel = GlobalVariable.params["logLevel"]
    if logLevel == "info":
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    elif logLevel == "debug":
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    elif logLevel == "error":
        logging.basicConfig(level=logging.ERROR, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    logging.info("获取配置 "+json.dumps(GlobalVariable.params))
    # 初始化线程池
    threadParams = GlobalVariable.params["params"]["threadPool"]
    GlobalVariable.BroachPool = BroachPool.Pool(core=int(threadParams["core"]),
                                                threadMax=int(threadParams["threadMax"]),
                                                keepAliveTime=int(threadParams["keepAliveTime"]),
                                                queue=BroachPool.ArrayQueue(
                                                    queueMax=int(threadParams["queueMax"]),
                                                    isExcInfo=threadParams["isExcInfo"] == "True" or threadParams["isExcInfo"] == "true",
                                                    createThreadThreshold=int(threadParams["createThreadThreshold"])),
                                                poolName="BroachPool")
    # 启动服务端进程
    server = RpcServer.RpcServer()
    server.start()

def getConfig(path):
    with open(path, encoding="utf-8") as f:
        getJson = json.load(f)
    GlobalVariable.params = getJson


run()
