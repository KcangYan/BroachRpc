#appName
name = "BroachRpc"
#版本
version = "1.0"
#日志级别
logLevel = "info"
#配置
params = {
    "rpcPort": 18081,
    "rpcIp": "127.0.0.1",
    "rpcTimeOut": 6,
    "udpTimeOut": 3,
    "threadPool" : {
      "core" : 3,
      "threadMax" : 15,
      "keepAliveTime" : 9,
      "queueMax" :  1000,
      "isExcInfo" : "False",
      "createThreadThreshold" : 2
    }
  }
#全局线程池
BroachPool = None
#本机函数路由映射
FuncRoute = {}
#udp缓冲区大小
BufferLen = 3028
#NES类udp消息间隔重传
IntervalUdp = 0.15
#定时任务组 [{ "fn": fn, "timeStep": 6 }]
TimerTasks = []
