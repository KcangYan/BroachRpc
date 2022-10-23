import BroachApply
from common import GlobalVariable
import BroachFramework

BroachFramework.run()

@BroachApply.rpcCall()
def t(*args, **kwargs):
    print("t")

@BroachApply.rpcRoute()
def work01():
    print("work01"+GlobalVariable.params.get("rpcIp") + ":" + GlobalVariable.params.get("rpcIp"))


