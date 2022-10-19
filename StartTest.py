import BroachFramework

@BroachFramework.rpcCall()
def t(*args, **kwargs):
    print("t")

t("1019")


