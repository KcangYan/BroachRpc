import BroachApply
from common import GlobalVariable
import BroachFramework

#BroachFramework.run()

d = {"a":{"a1":1, "a2":2}, "b":2}
print(d)
i1 = d.get("a")
i1["a1"]=3
print(d)

@BroachApply.rpcCall()
def t(*args, **kwargs):
    print("t")

@BroachApply.rpcRoute()
def work01():
    print("work01"+GlobalVariable.params.get("rpcIp") + ":" + GlobalVariable.params.get("rpcIp"))


