from common import *
from common.utils import *
from source.source_tushare import TushareSource
import logging
import argparse
import yaml
import importlib
import threading
from concurrent.futures import ThreadPoolExecutor

def init():
    logger = logging.getLogger(__name__)  
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler('/Users/bytedance/DeepLearningStock/my.log')
    formatter = logging.Formatter('%(asctime)s : %(name)s  : %(funcName)s : %(levelname)s : %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return 

class Engine():
    def __init__(self, yaml_path):
        ## 载入yaml配置文件
        self.conf = yaml.safe_load(open(yaml_path, 'r') .read())

        ## source_mutext 多线程同时处理context，获取context时加锁
        self.source_mutex = threading.Lock()
        self.context_num = 0
        logging.error(pretty_json(self.conf))
        return 

    def get_obj_by_conf(self, conf):
        """
            给定配置的path + class name, 和类的参数，返回对象
        """
        module = importlib.import_module(conf["path"])
        my_class = getattr(module, conf["class"])
        args = conf.get("args", {})
        obj = my_class(args)
        return obj

    def init_sources(self):
        # 初始化所有source
        source_list = self.conf["source"]["source_list"]
        self.sources = []
        for source in source_list:
            self.sources.append(self.get_obj_by_conf(source))
        # source idx表示当前读到了第几个source
        self.source_cursor = 0
        return 

    def get_context(self):
        # 互斥锁
        with self.source_mutex:
            # 整个队列用完了
            while self.source_cursor < len(self.sources): 
                cur_source = self.sources[self.source_cursor]
                context = cur_source.get_context()
                if context is None:
                    # 当前source用完了
                    self.source_cursor += 1 
                else:
                    return context
            return 
    def init_steps(self):
        """
          获取所有的step
        """
        step_list = self.conf["step"]["step_list"]
        if step_list is None:
            step_list = []
        self.steps = []
        self.name2step = {}
        for step in step_list:
            name = step["name"]
            step_obj = self.get_obj_by_conf(step)
            step_obj.name = name
            self.steps.append(step_obj)
            self.name2step["name"] = step_obj
        return self.steps
    
    def process_context_thread_fun(self, thread_idx):
        print('线程启动')
        process_context =0 
        while True:
            context = self.get_context()
            if context is None:
                break
            # step 逐一执行
            for step in self.steps:
                step.execute(context)
            self.context_num += 1
            process_context += 1
            if self.context_num % 100 == 0:
                # print(context)
                logging.error("[thread-%s] context_num: %s %s cur source: %s" %(thread_idx, self.context_num, 
                                context.id, self.sources[self.source_cursor].get_progress()))
        return process_context
    
    def multithread_run(self):
        """
        conf: yaml配置文件
        """
        time_start = time.time()
        ## 初始化source
        self.init_sources()
        ## 一个step一个step执行
        self.init_steps()
        thread_num = self.conf.get("thread_num", 5)
        # input("thread_num: %s" %(thread_num))
        # threads = []
        # for i in range(thread_num):
        #     t = threading.Thread(target = self.process_context_thread_fun, args=(self, )) 
        #     threads.append(t)
        # for t in threads:
        #     t.start()
        # for t in threads:
        #     t.join()
        # 线程池写法
        thread_pool = ThreadPoolExecutor(max_workers=10)
        futures = []
        for i in range(thread_num):
            future = thread_pool.submit(self.process_context_thread_fun, i+1)
            futures.append(future)
        for f in futures:
            print("线程result: %s" %(f.result()))
        
        # 分source耗时:
        for source in self.sources:
            print("[source-%s] 耗时: %.1f秒" %(type(source).__name__, source.time_cost))
        # 分step耗时:
        for step in self.steps:
            print("[step-%s] 耗时:%.1f秒" %(type(step).__name__, step.time_cost))
        latency = time.time() - time_start
        logging.error("[main end] 总context数: %s, 耗时: %.1fs" %(self.context_num, latency))
        return 

    def run(self):
        """
        conf: yaml配置文件
        """
        ## 初始化source
        self.init_sources()
        ## 一个step一个step执行
        self.init_steps()
        context_num = 0
        time_start = time.time()
        while True:
            context = self.get_context()
            if context is None:
                break
            # step 逐一执行
            for step in self.steps:
                step.execute(context)
            context_num += 1
            if context_num % 100 == 0:
                # print(context)
                logging.error("[main progress] context_num: %s %s cur source: %s" %(context_num, 
                                context.id, self.sources[self.source_cursor].get_progress()))
        # 分step耗时:
        for step in self.steps:
            print("[step-%s] 耗时:%.1f秒" %(step.__name__, step.time_cost))
        latency = time.time() - time_start
        logging.error("[main end] 总context数: %s, 耗时: %.1fs" %(context_num, latency))
        return 

if __name__ == "__main__":
    init()
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='yaml配置文件', default = "tushare.yaml") 
    args = parser.parse_args()
    engine = Engine(args.config)
    engine.multithread_run()
    # engine.run()