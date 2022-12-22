from common.utils import *
from step.step import Step
from common.stock_pb2 import *
import time
import struct
from queue import Queue
import threading

class WriteInstanceStep(Step):
    def __init__(self, conf):
        super(WriteInstanceStep, self).__init__(conf)
        # 要保存的文件
        save_path = conf.get("save_path", "../training_data/data.bin")
        date_suffix = conf.get("date_suffix", "%Y%m%d") 
        self.save_file = "%s.%s" %(save_path, timestamp2str(time.time(), date_suffix))
        self.f = open(self.save_file, "wb") 
        self.cache_size = conf.get("cache_size", 30)
        self.cache = Queue()
        # 
        self.write_mutex = threading.Lock()
        self.write_raw_feature = conf.get("write_raw_feature", False)
        return 
    
    def __del__(self):
        print("write_instance最后写入")
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
        total_mv = context.get("raw_feature.basic.total_mv") 
        ins.total_mv = 0 if total_mv == "EMPTY" else int(total_mv)
        # fid
        feature2data = context.get("fids")
        for key in feature2data:
            fc = FeatureColumn()
            slot, fids, raw_feature, extracted_features = feature2data[key]
            fc.name = key
            fc.slot = slot 
            fc.fids.extend(fids)

            if self.write_raw_feature:
                fc.raw_feature.extend([str(item) for item in raw_feature])
            fc.extracted_features.extend(extracted_features)
            ins.feature.extend([fc])
        # label
        labels = context.get("label")
        for k in labels:
            ins.label[k] = labels[k]
        # 存到context， debug
        context.set("pack_instance", ins)
        return ins
    
    def write_instance(self):
        self.write_mutex.acquire()
        # 把二进制数据+字节数写到文件中: 写到队列为空或者写cache个
        write_cnt = self.cache_size
        print("wriet_instance: size: %s" %(self.cache.qsize()))
        while not self.cache.empty() and write_cnt > 0:
            item = self.cache.get()
            write_file_with_size(self.f, item.SerializeToString()) 
            write_cnt -= 1
        self.write_mutex.release()
        return 

    def add_instance(self, ins):
        """
          instance加入cache中
        """
        self.cache.put(ins)
        return 

    def _execute(self, context): 
        ins = self.pack_instance(context)
        self.add_instance(ins)
        # cache数足够了，则写文件
        if self.cache.qsize() >= self.cache_size:
            self.write_instance()
        return 
