import asyncio
import time
import threading

lock = threading.Condition()

async def work1(x):
    #lock.acquire()
    #lock.wait(2)
    #lock.release()
    print("work1-1: "+x)
    await asyncio.sleep(2)
    print("work1-2: "+x)
    return x

async def work2(x):
    print("work2-1: " + x)

    print("work2-2: " + x)
    return x

def callback(future):
    print("获得返回值: "+ future.result())

a = work1("1")
b = work2("2")
loop = asyncio.get_event_loop() # 创建事件循环
#task = asyncio.wait([a,b])# 创建task任务
task1 = loop.create_task(a)
task1.add_done_callback(callback)
task2 = loop.create_task(b)
task2.add_done_callback(callback)
tasks = asyncio.wait([task1, task2])
loop.run_until_complete(tasks) # 把协程对象丢给循环,并执行异步函数内部代码
asyncio.Queue()