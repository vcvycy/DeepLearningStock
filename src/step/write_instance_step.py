from common.utils import *
from step.step import Step
from common.stock_pb2 import *
import time
import struct
class WriteInstanceStep(Step):
    def __init__(self, conf):
        super(WriteInstanceStep, self).__init__(conf)
        # 要保存的文件
        save_path = conf.get("save_path", "../training_data/")
        suffix = timestamp2str(time.time(), "%Y%m%d")
        self.save_file = "%s/data.bin.%s" %(save_path, suffix)
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
    
    def save_instance(self, ins):
        """
          保存instance
        """
        f = open(self.save_file, "ab") 
        # 把二进制数据+字节数写到文件中
        write_file_with_size(f, ins.SerializeToString()) 
        f.close()
        return 

    def execute(self, context): 
        ins = self.pack_instance(context)
        self.save_instance(ins)
        return 
