import BroachApply
import BroachFramework
import time
from common import GlobalVariable

BroachFramework.run("./application2.json")

@BroachApply.rpcCall(name="work00")
def t0(*args, **kwargs):
    pass
@BroachApply.rpcCall(name="work01")
def t1(*args, **kwargs):
    pass
@BroachApply.rpcCall(name="work02")
def t2(*args, **kwargs):
    pass

time.sleep(6)
print("调用开始")
print(GlobalVariable.FuncRouteRpc)
for i in range(0,10):
    print(t0())
print(t1(1,2))
print(t2(1,2))

