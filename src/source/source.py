from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue
"""
  每个Source维护一个queue(context_queue): 
     1. add_context 加入一个context
     2. get_context 读取一个context
"""
class Source:
    def __init__(self, conf):
        self.conf = conf
        # 一次取多个context，保存在context_queue
        self.context_queue = Queue()     # context队列
        # 线程池, 多线程取context
        self.context_size = 0       # 用于debug
        self.context_consumed = 0
        return

    def add_context(self, context):
        self.context_size += 1 
        self.context_queue.put(context) 
        return 
    
    def get_context(self): 
        while True:
            all_finish = self.is_all_thread_done()
            try:
                # 取数据, 0.1秒超时
                ctx =  self.context_queue.get(timeout = 0.1)
                self.context_consumed += 1
                return ctx
            except:
                # 取数据超时且在取数前, 所有线程都跑完了, 则返回None
                if all_finish:
                    return None 
    
    def get_progress(self):
        # 当前source的进度
        raise Exception("need override")

class MultiThreadSource(Source):  # 多线程source
    def __init__(self, conf):
        super(MultiThreadSource, self).__init__(conf)
        max_workers = conf.get("max_workers", 30)
        self.max_thread = conf.get("max_thread", 99999)
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.futures = []
        return 
    
    # 新增一个线程，取数据，写到context_queue
    def add_thread(self, func, *args, **kwargs):
        # 线程池初始化  
        if len(self.futures) >= self.max_thread :
            return 
        future = self.thread_pool.submit(func, self, *args, **kwargs)
        self.futures.append(future)  

    def get_thread_finish_num(self):
        cnt = 0
        for f in self.futures:
            if f.done():
                cnt += 1
        return cnt

    # 是否全部线程执行完成
    def is_all_thread_done(self):
        for f in self.futures:
            if not f.done():
                return False
        return True

    def get_progress(self):
        all_threads = len(self.futures)
        finished_thread = self.get_thread_finish_num()
        return "进程完成数: %s/%s" %(finished_thread, all_threads)

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
        