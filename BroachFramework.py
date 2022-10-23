from threadPool import BroachPool
from common import GlobalVariable
import json
import logging
from network import RpcService

"""
框架主启动入口
"""
def run(path='./application.json'):
    # 初始化配置
    getConfig(path)
    # 初始化日志配置
    LOG_FORMAT = '%(asctime)s -%(name)s- %(threadName)s-%(thread)d - %(levelname)s - %(message)s'
    DATE_FORMAT = "%Y/%m/%d %H:%M:%S %p"
    logLevel = GlobalVariable.logLevel
    if logLevel == "info":
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    elif logLevel == "debug":
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    elif logLevel == "error":
        logging.basicConfig(level=logging.ERROR, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
    logging.info("获取配置 " + json.dumps(GlobalVariable.params))
    # 初始化线程池
    threadParams = GlobalVariable.params["threadPool"]
    GlobalVariable.BroachPool = BroachPool.Pool(core=int(threadParams["core"]),
                                                threadMax=int(threadParams["threadMax"]),
                                                keepAliveTime=int(threadParams["keepAliveTime"]),
                                                queue=BroachPool.ArrayQueue(
                                                    queueMax=int(threadParams["queueMax"]),
                                                    isExcInfo=threadParams["isExcInfo"] == "True" or threadParams["isExcInfo"] == "true",
                                                    createThreadThreshold=int(threadParams["createThreadThreshold"])),
                                                poolName="BroachPool")
    RpcService.instance = RpcService.RpcService()
    # 启动服务端进程
    RpcService.instance.serverStart()

def getConfig(path):
    with open(path, encoding="utf-8") as f:
        getJson = json.load(f)
    if getJson.get("name") is not None:
        GlobalVariable.name = getJson.get("name")
    if getJson.get("version") is not None:
        GlobalVariable.version = getJson.get("version")
    if getJson.get("logLevel") is not None:
        GlobalVariable.logLevel = getJson.get("logLevel")
    if getJson.get("params") is not None:
        params = getJson.get("params")
        if params.get("rpcPort") is not None:
            GlobalVariable.params["rpcPort"] = params.get("rpcPort")
        if params.get("rpcIp") is not None:
            GlobalVariable.params["rpcIp"] = params.get("rpcIp")
        if params.get("clusterAddress") is not None:
            GlobalVariable.params["clusterAddress"] = params.get("clusterAddress")
        if params.get("rpcTimeOut") is not None:
            GlobalVariable.params["rpcTimeOut"] = params.get("rpcTimeOut")
        if params.get("udpTimeOut") is not None:
            GlobalVariable.params["udpTimeOut"] = params.get("udpTimeOut")
        if params.get("threadPool") is not None:
            threadPool = params.get("threadPool")
            if threadPool.get("core") is not None:
                GlobalVariable.params["threadPool"]["core"] = threadPool.get("core")
            if threadPool.get("threadMax") is not None:
                GlobalVariable.params["threadPool"]["threadMax"] = threadPool.get("threadMax")
            if threadPool.get("keepAliveTime") is not None:
                GlobalVariable.params["threadPool"]["keepAliveTime"] = threadPool.get("keepAliveTime")
            if threadPool.get("queueMax") is not None:
                GlobalVariable.params["threadPool"]["queueMax"] = threadPool.get("queueMax")
            if threadPool.get("isExcInfo") is not None:
                GlobalVariable.params["threadPool"]["isExcInfo"] = threadPool.get("isExcInfo")
            if threadPool.get("createThreadThreshold") is not None:
                GlobalVariable.params["threadPool"]["createThreadThreshold"] = threadPool.get("createThreadThreshold")
