from common.utils import *
from step.step import Step
from common.stock_pb2 import *
import time
import struct
from queue import Queue
class WriteInstanceStep(Step):
    def __init__(self, conf):
        super(WriteInstanceStep, self).__init__(conf)
        # 要保存的文件
        save_path = conf.get("save_path", "../training_data/data.bin")
        date_suffix = conf.get("date_suffix", "%Y%m%d") 
        self.save_file = "%s.%s" %(save_path, timestamp2str(time.time(), date_suffix))
        self.f = open(self.save_file, "ab") 
        self.cache_size = conf.get("cache_size", 30)
        self.write_raw_feature = conf.get("write_raw_feature", False)
        self.cache = Queue()
        return 
    
    def __del__(self):
        self.write_instance()
        return 
    
    def pack_instance(self, context):
        """
          组装训练数据
        """
        ins = Instance()
        # 通用字段
        ins.name = context.get("source.name")
        ins.ts_code = context.get("source.ts_code")
        ins.date = context.get("source.train_date")
        # fid
        key2fids = context.get("fids")
        for key in key2fids:
            fc = FeatureColumn()
            fc.name = key 
            fc.fids.extend(key2fids[key])
            ins.feature.extend([fc])
        # label

        # 存到context， debug
        context.set("pack_instance", ins)
        return ins
    
    def write_instance(self):
        # 把二进制数据+字节数写到文件中
        while not self.cache.empty():
            item = self.cache.get()
            write_file_with_size(self.f, item.SerializeToString()) 
        return 

    def add_instance(self, ins):
        """
          instance加入cache中
        """
        self.cache.put(ins)
        return 

    def execute(self, context): 
        ins = self.pack_instance(context)
        self.add_instance(ins)
        # cache数足够了，则写文件
        if self.cache.qsize() >= self.cache_size:
            self.write_instance()
        return 
