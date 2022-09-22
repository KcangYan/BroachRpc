import BroachFramework
from apply import Component
from config import GlobalVariable
from network import MsgHandler

BroachFramework.run()

from network import RpcClient,MsgHandler
from apply import FuncSignal
import time
import logging
time.sleep(2)

msg = ""
for i in range(0,1000):
    msg = msg + "hello word "


def t1(*args, **kwargs):
    test = {"funcId": "work", "args": args, "kwargs": kwargs, "reqId": MsgHandler.getId(18), "orgId": "0"}
    logging.info(FuncSignal.callRpc(test, "127.0.0.1", 18080))

@Component.rpcRoute()
def work(x,y):
    print(x)
    print(y)
    return "work"

t1(x=1)