from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue
class Source:
    def __init__(self, conf):
        self.conf = conf
        # 一次取多个context，保存在context_cache
        self.context_cache = Queue()     # context队列
        self.context_rw_lock = threading.Lock()
        # 线程池, 多线程取context
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        self.futures = []
        self.context_size = 0
        self.context_consumed = 0
        return

    # 新增一个线程，取数据，写到context_cache
    def add_thread(self, func, *args, **kwargs):
        # 线程池初始化 
        self.futures.append(self.thread_pool.submit(func, self, *args, **kwargs)) 

    # 是否全部线程执行完成
    def is_thread_done(self):
        for f in self.futures:
            if not f.done():
                return False
        return True

    def add_context(self, context):
        self.context_size += 1 
        self.context_cache.put(context) 
        return 
    
    def get_context(self): 
        while True:
            all_finish = self.is_thread_done()
            try:
                # 取数据, 0.1秒超时
                ctx =  self.context_cache.get(timeout = 0.1)
                self.context_consumed += 1
                return ctx
            except:
                # 取数据超时且在取数前, 所有线程都跑完了, 则返回None
                if all_finish:
                    return None

if __name__ == "__main__":
    import time
    def add(queue, x, y):
        for i in range(x, y):
            queue.put(i)
        return 
    src = Source({})
    src.add_thread(add, 6,10)
    src.add_thread(add, 15,20)  
    while True:
        ctx = src.get_context()
        if ctx is None:
            break
        print(ctx)
        