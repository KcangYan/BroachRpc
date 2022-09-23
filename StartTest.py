import BroachFramework
from apply import Component
from common import CommonDef

BroachFramework.run()

from network import RpcService
import time
import logging
time.sleep(2)

def t1(*args, **kwargs):
    return RpcService.RpcService().sendRpc("127.0.0.1", 18080, "work", *args, **kwargs)

@Component.rpcRoute()
def work(x,y):
    print(x)
    print(y)
    return "hello broach"

logging.info(t1(1,2))

