from common.utils import *
from common.stock_pb2 import *
import numpy as np
import yaml
import logging
# from common.tushare_api import *
# 全局通用

class RM: 
    def __init__(self, conf_file):
        # 全局字段定义
        self.conf_file = conf_file
        self.conf = yaml.safe_load(open(conf_file, 'r') .read())
        self.all_dates = []   # 所有日期, 从小到大排序
        self.date2thre = {}   # 每一天取一个label阈值
        self.instances =[]    # 所有训练样本
        # logging初始化
        train_files = self.conf.get("train_files")
        suffix = train_files[0].split(".")[-1] 
        self.log_file = "%s.%s" %(self.conf.get("log_file"), suffix)
        print("日志文件： %s" %(self.log_file))
        logging.basicConfig(filename=self.log_file, format = '%(levelname)s %(asctime)s %(message)s', level=logging.DEBUG)
        logging.info("conf: %s" %(self.conf)) 
        # 读取instance并初始化
        date2labels = {}
        max_ins = self.conf.get("max_ins")
        for ins in enum_instance(train_files, max_ins if max_ins is not None else 1e10):
            date = ins.date
            label_key = self.conf["train_data"]["label"]["args"]["key"]
            if label_key in ins.label:
                date2labels[date] = date2labels.get(date, [])
                date2labels[date].append(ins.label[label_key]) 
            self.instances.append(ins)

        self.all_dates = list(date2labels)
        self.all_dates.sort()

        for date in self.all_dates: 
            labels = date2labels[date]
            self.date2thre[date] = np.percentile(labels, 50)   # 每天50分位置
            logging.info("%s 样本数: %s pct 50 label: %.3f" %(date,len(labels), self.date2thre[date])) 
        logging.info("总训练样本: %s" %(len(self.instances)))
        return 
# 单例
__global_rm = None
def init_singleton_rm(conf_file):
    global __global_rm
    __global_rm = RM(conf_file)
    return 
def get_rm():
    global __global_rm
    return __global_rm

if __name__ == "__main__":
    assert "在model_train中测试"