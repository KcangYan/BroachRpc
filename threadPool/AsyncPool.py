import asyncio

async def work1(x):
    print(x)

loop = asyncio.get_event_loop() # 创建事件循环
loop.run_until_complete(work1("hello")) # 把协程对象丢给循环,并执行异步函数内部代码
