import BroachFramework

BroachFramework.run()

from network import RpcClient,RpcHandler
import time
import logging
time.sleep(1)
msgId = "kcang1590"
msg = ""
for i in range(0, 1000):
    msg = msg + "test "
logging.info(RpcClient.Client.sendNES(msgId, msg, "127.0.0.1", 18081))

time.sleep(15)
logging.info(RpcHandler.getNESRev(RpcClient.Client.id, msgId))