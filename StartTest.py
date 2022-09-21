import BroachFramework
from apply import Component

BroachFramework.run()

from network import RpcClient,RpcHandler
from apply import FuncSignal
import time
import logging
time.sleep(2)

msg = ""
for i in range(0,1000):
    msg = msg + "hello word "

test = {"funcId": "work", "args": None }
print(FuncSignal.callRpc(test, "127.0.0.1", 18080))

@Component.rpcRoute()
def work(x,y):
    print(x)
    print(y)
    return "work"