import BroachApply
import BroachFramework
import time
from common import GlobalVariable

BroachFramework.run("./application1.json")

@BroachApply.rpcRoute()
def work00():
    return "127.0.0.1:18081"

@BroachApply.rpcRoute()
def work02(x,y):
    return (x+y)*2

while True:
    #print(GlobalVariable.FuncRouteRpc)
    #print(GlobalVariable.FuncRoute)
    time.sleep(1)