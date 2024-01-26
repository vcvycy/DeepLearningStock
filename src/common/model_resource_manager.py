from common.utils import *
from common.stock_pb2 import *
import numpy as np
import yaml
import logging
import re
# from common.tushare_api import *
class RM: 
    def ins_need_filter(self, ins, filters):
        if filters["only_etf"]:
            return "ETF" not in ins.name #or "LOF" not in ins.name
        if "valid_tscode" in filters:
            name = "valid_tscode" 
            conf = filters[name]
            reg = conf["regexp"]
            if conf.get("enable"):
                if len(re.findall(reg, ins.ts_code)) == 0:
                    self.filter_reason[name] = self.filter_reason.get(name, 0) + 1
                    return True
        if "fid_filter" in filters:
            conf = filters["fid_filter"]
            if conf.get("enable"): 
                filter_fids = set(conf.get("fids"))
                for fc in ins.feature:  
                    for fid in fc.fids:
                        if fid in filter_fids:
                            need_filter = True
                            r = "fid_filter_%s" %(fid)
                            self.filter_reason[r] = self.filter_reason.get(r, 0) + 1
                            return True
        # 退市股过滤
        if "退" in ins.name:
            self.filter_reason["退市"] = self.filter_reason.get("退市", 0) + 1
            return True
        return False
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
        self.json_result_file = "%s.%s" %(self.conf.get("json_result"), suffix)
        print("日志文件： %s" %(self.log_file))
        logging.basicConfig(filename=self.log_file, format = '%(levelname)s %(asctime)s %(message)s', level=logging.DEBUG)
        logging.info("conf: %s" %(self.conf)) 
        filters = self.conf.get("train_data").get("filters")
        # 读取instance并初始化
        date2labels = {}
        max_ins = self.conf.get("max_ins")
        self.filter_reason = {}
        for ins in enum_instance(train_files, max_ins if max_ins is not None else 1e10):
            if ins.date < '20200601':
                continue
            if self.ins_need_filter(ins, filters):
                continue
            date = ins.date
            label_key = self.conf["train_data"]["label"]["args"]["key"]
            if label_key in ins.label:
                date2labels[date] = date2labels.get(date, [])
                date2labels[date].append(ins.label[label_key]) 
            self.instances.append(ins)
        logging.info("样本filter: %s" %(len(self.filter_reason)))
        for filter in self.filter_reason:
            logging.info("  样本filter: %s : %s" %(filter, self.filter_reason[filter]))
            
        self.all_dates = list(date2labels)
        self.all_dates.sort()
        # 获取验证集的日期
        train_ins_percent = self.conf.get("train_data").get("train_ins_percent")
        if train_ins_percent is not None:
            train_ins_num = 0
            for date in self.all_dates:
                if train_ins_num >= train_ins_percent * len(self.instances):
                    self.validate_date = date
                    break
                train_ins_num += len(date2labels.get(date, []))
            logging.info("训练集占比: %s 训练集样本数量: %s / %s" %(train_ins_percent, train_ins_num, len(self.instances)))
        else:
            self.validate_date = self.conf.get("train_data").get("validate_date")
        logging.info("验证集开始时间: %s" %(self.validate_date))
        # 每个日期对应的大盘均值
        for date in self.all_dates: 
            labels = date2labels[date]
            labels.sort(key = lambda x : x)
            pct = 50
            self.date2thre[date] = np.percentile(labels, pct)   # 每天50分位置
            logging.info("%s 样本数: %s pct %s label: %.3f" %(date,len(labels), pct, self.date2thre[date])) 
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