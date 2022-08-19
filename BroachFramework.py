class MyList(object):
    def __init__(self):
        self.my_list = list()
        self.current_index = 0
    # 添加指定元素
    def append_item(self, item):
        self.my_list.append(item)
    def __iter__(self):
        # 可迭代对象的本质：遍历可迭代对象的时候其实获取的是可迭代对象的迭代器， 然后通过迭代器获取对象中的数据
        print("????????")
        yield self
    def __next__(self):
        if self.current_index < len(self.my_list):
            self.current_index += 1
            return self.my_list[self.current_index - 1]
        else:
            # 数据取完了，需要抛出一个停止迭代的异常
            raise StopIteration

def fibonacci(num):
    a = 0
    b = 1
    # 记录生成fibonacci数字的下标
    current_index = 0
    print("--生成器初始化---")
    while current_index < num:
        result = a
        a, b = b, a + b
        current_index += 1
        print("--开始生产---")
        # 代码执行到yield会暂停，然后把结果返回出去，下次启动生成器会在暂停的位置继续往下执行
        yield result
        print("--结束生产---")
        yield result+1

my_list = MyList()
my_list.append_item(1)
my_list.append_item(2)
while True:
    try:
        value = next(my_list)
        print(value)
    except StopIteration as e:
        break

fib = fibonacci(2)
value = next(fib)
print(value)
value = next(fib)
print(value)
#for value in fib:
#     print(value)

import greenlet
import time
from gevent import monkey

# 打补丁，让gevent框架识别耗时操作，比如：time.sleep，网络请求延时
monkey.patch_all()
def work1():
    for i in range(5):
        print("work1...")
        time.sleep(0.2)
        # 切换到协程2里面执行对应的任务
        g2.switch()

def work2():
    for i in range(5):
        print("work2...")
        time.sleep(0.2)
        # 切换到第一个协程执行对应的任务
        g1.switch()
g1 = greenlet.greenlet(work1)
g2 = greenlet.greenlet(work2)
g1.switch()

import gevent
def work(n):
    for i in range(n):
        # 获取当前协程
        print(gevent.getcurrent(), i)
        #gevent.sleep(2)
        time.sleep(2)
gv1 = gevent.spawn(work, 5)
gv2 = gevent.spawn(work, 5)
gv3 = gevent.spawn(work, 5)
while True:
    print("主线程开始")
    time.sleep(1)
#gv1.join()
#gv2.join()
#gv3.join()
