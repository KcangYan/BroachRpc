import json

import logging

LOG_FORMAT = '%(asctime)s -%(name)s- %(threadName)s-%(thread)d - %(levelname)s - %(message)s'
DATE_FORMAT = "%Y/%m/%d %H:%M:%S %p"
#日志配置
#logging.basicConfig(level=logging.INFO,format=LOG_FORMAT,datefmt=DATE_FORMAT)

class Config:

    def __init__(self, path):
        self.path = path
        #logging.info("加载配置文件 "+path)
        with open(path, encoding="utf-8") as f:
            self.json = json.load(f)
        #logging.info("获取配置 "+json.dumps(self.json))
        self.name = self.json["name"]
        self.version = self.json["version"]
        self.params = self.json["params"]
        if self.json["logLevel"] == "info":
            logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
        if self.json["logLevel"] == "debug":
            logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)
        if self.json["logLevel"] == "error":
            logging.basicConfig(level=logging.ERROR, format=LOG_FORMAT, datefmt=DATE_FORMAT)
        logging.info("获取配置 "+json.dumps(self.json))

    def getParam(self, key=None):
        if key is None:
            return self.params
        else:
            try:
                return self.params[key]
            except KeyError:
                return None

    def getName(self):
        return self.name

    def getVersion(self):
        return self.version

