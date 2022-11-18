import BroachApply
import BroachFramework
import time
from common import GlobalVariable

BroachFramework.run()

@BroachApply.rpcRoute()
def work00():
    return "127.0.0.1:18080"

@BroachApply.rpcRoute()
def work01(x,y):
    return x+y

while True:
    #print(GlobalVariable.FuncRouteRpc)
    #print(GlobalVariable.FuncRoute)
    time.sleep(1)