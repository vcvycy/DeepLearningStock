from common import *
from common.utils import *
from source.source_tushare import TushareSource
import logging
import argparse
import yaml
import importlib
import threading

def init():
    logger = logging.getLogger(__name__)  
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler('/Users/bytedance/DeepLearningStock/my.log')
    formatter = logging.Formatter('%(asctime)s : %(name)s  : %(funcName)s : %(levelname)s : %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return 

class Engine():
    def __init__(self, yaml_path, thread_num):
        ## 载入yaml配置文件
        self.conf = yaml.safe_load(open(yaml_path, 'r') .read())

        ## source_mutext 多线程同时处理context，获取context时加锁
        self.source_mutex = threading.Lock()
        self.thread_num = thread_num

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
        self.source_mutex.acquire()
        # 整个队列用完了
        if self.source_cursor >= len(self.sources):
            return
        cur_source = self.sources[self.source_cursor]
        context = cur_source.get_context()
        if context is None:
            # 当前source用完了
            self.source_cursor += 1
            return self.get_context()
        # 去锁
        self.source_mutex.release()
        return context

    def init_steps(self):
        """
          获取所有的step
        """
        step_list = self.conf["step"]["step_list"]
        self.steps = []
        self.name2step = {}
        for step in step_list:
            name = step["name"]
            step_obj = self.get_obj_by_conf(step)
            step_obj.name = name
            self.steps.append(step_obj)
            self.name2step["name"] = step_obj
        return self.steps
    
    def run(self):
        """
        conf: yaml配置文件
        """
        ## 初始化source
        self.init_sources()
        ## 一个step一个step执行
        self.init_steps()
        while True:
            context = self.get_context()
            if context is None:
                break
            # step 逐一执行
            for step in self.steps:
                step.execute(context)
        return 

if __name__ == "__main__":
    init()
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='yaml配置文件', default = "tushare.yaml") 
    parser.add_argument('--thread_num', default = 1)
    args = parser.parse_args()
    engine = Engine(args.config, args.thread_num)
    engine.run()