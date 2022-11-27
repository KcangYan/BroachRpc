###一个基于udp协议的RPC框架  BroachRpc

**框架特点**
~~~~text
1. 无注册中心模式，采用”蔓延感染“的思路，将当前上线主机及其提供的服务注册到集群里
的所有机器的路由表
2. 所有通信基于udp实现
3. 客户端自带负载均衡
4. 开箱即用，使用python装饰器配置路由和调用即可，无需其他组件辅助。使用起来便捷简单。
5. 下线主机会自动熔断，直接报错返回
6. 负载模式扩展和自定义(开发中，目前只支持均衡负载)
~~~~

**配置参数**
~~~python
#参数路径导入框架主启动项，目前只支持json文件
BroachFramework.run("./application1.json")
~~~~

~~~~json
{
  "name": "BroachRpc",
  "version": "1.0.0",
  "logLevel": "debug",
  "params": {
    "rpcPort": 18080,
    "rpcIp": "127.0.0.1",
    "clusterAddress" : ["127.0.0.1:18080"],
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
}
~~~~
~~~~text
  参数解释：
  name 实例主机或服务名
  version 服务版本号
  logLevel 框架日志打印级别
  系统参数params
    rpcPort 当前实例主机rpc服务接收端口
    rpcIp 当前实例主机rpc服务接收地址
    clusterAddress 配置蔓延地址，指向当前运行的RPC集群中的某一台或多台存活的主机即可
    rpcTimeOut rpc调用超时时间
    udpTimeOut 底层udp双向协议超时时间
  框架内部线程池threadPool配置
    core 核心线程数
    threadMax 最大线程数
    keepAliveTime 空闲线程存活时间 秒 
    queueMax 线程池任务队列长度
    isExcInfo 线程池任务队列溢出以后 true为报错 false为交由提交任务的线程执行溢出任务
    createThreadThreshold 当队列任务数任务超过此项值时 创建新线程消费任务
~~~~

**启动与使用**

~~~~python
from BroachRpc import BroachFramework,BroachApply

#启动框架，框架启动函数为异步函数 不会阻塞当前线程
BroachFramework.run("./application1.json")

#服务提供端 默认使用函数名作为服务名
@BroachApply.rpcRoute()
def work00():
    return "127.0.0.1:18080"

@BroachApply.rpcRoute(name="自定义服务名")
def work01(x,y):
    return x+y

#服务调用者 默认使用函数名去调用
@BroachApply.rpcCall()
def work00(*args, **kwargs):
    pass
@BroachApply.rpcCall(name="work01")
def t1(*args, **kwargs):
    pass
@BroachApply.rpcCall(name="work02")
def t2(*args, **kwargs):
    pass

#在需要的地方使用配置了rpcCall装饰器的函数即可调用集群中的函数
work00()
t1(1,2)
t2(2,3)
~~~~

**原理简述**

~~~~text
1. 底层通信使用udp作为消息协议是因为我认为在rpc调用的场景中应该都是服务器与服务器之间的通信
甚至大部分集群都在同一个内网网段下，几乎不存在udp消息丢失的问题。
2. 虽然几乎不存在udp消息丢失的情况但框架还是参考了QUIC协议设计了一个应答模式保证消息的送达与响应
具体实现如下
2.1 当rpc消息发起时，A服务器发送一个udp包到B服务器同时A服务器阻塞等待B服务器的udp包回答
如果超时不回答则放弃此次通信直接结束。
2.2 包消息中有请求id 和 响应id来区分发送和接收的是请求包还是响应包。当收到对应请求id的响应包时，
框架会结束请求线程的阻塞并将响应结果返给请求线程
2.3 同时诸如注册 心跳维护等等框架系统级别的信息交互则直接采用udp通信不做响应回调，毕竟服务器之间
如果长时间udp包都无法得到回应的话，则认为对方掉线也没什么问题。
3. 无注册中心模式，参考redis集群的扩展，新实例上线时 只需配置rpc集群中的某一台节点的地址和端口即可
实现实例的接入和服务注册
具体实现如下
3.1 当前主机上线时 会向配置的地址请求当前所有的实例地址，收到回应后当前主机会向实例列表里所有
的主机发送一个上线通知，收到上线通知的主机会将当前主机加入到本机的实例列表里。
3.2 通知上线结束后当前主机会rpc调用内部函数将当前主机的服务注册到所有实例里，同时收到上线通知的主机也会将
本机的服务注册到当前主机的rpc路由表里
3.3 至此第一次上线完成。当第一次上线结束后，当前主机的实例列表里的主机如果没有全部响应，则会有定时任务朝这些
没有响应的主机发送上线通知直至全部主机都完成上线通知工作。
3.4 在定时任务中也会有心跳维护的能力，当实例列表中某些机器长时间没有心跳以后，则任务主机下线，在rpc调用时会
直接抛出异常终止调用，防止掉线主机占用过多通信线程导致任务堆积溢出。
~~~~


