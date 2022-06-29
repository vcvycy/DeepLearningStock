from common import *
from common.utils import *
from source.source_tushare import TushareSource
import logging
import argparse
import yaml
import importlib
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

    def fetch_one_context(self):
        # 整个队列用完了
        print("fetch")
        if self.source_cursor >= len(self.sources):
            return
        cur_source = self.sources[self.source_cursor]
        context = cur_source.fetch_one_context()
        if context is None:
            # 当前source用完了
            self.source_cursor += 1
            return self.fetch_one_context()
        return context

    def run(self):
        """
        conf: yaml配置文件
        """
        ## 初始化source
        self.init_sources()
        # 
        context = self.fetch_one_context()
        print(context)
        return 

if __name__ == "__main__":
    init()
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='yaml配置文件', default = "tushare.yaml") 
    args = parser.parse_args()
    engine = Engine(args.config)
    engine.run()