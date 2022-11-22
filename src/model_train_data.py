
from common.utils import *
from common.stock_pb2 import *
import logging
import yaml
import random
import tensorflow as tf
import logging
import numpy as np
def read_instances(files):
    if not isinstance(files, list):
        files = [files]
    instances = []
    for file in files:
        f = open(file, "rb")
        while True:
            size, data = read_file_with_size(f, Instance)
            if size == 0:
                break
            instances.append(data) 
    # logging.info("第一个Instance: %s" %(instances[0])) 
    logging.info("总训练样本: %s" %(len(instances)))
    return instances

class TrainItem():
    def __init__(self, fids, fid_indexs, label, date = "", ts_code = "", name = ""):
        # 这里的fid为过滤过的fid
        self.fids = fids
        self.label = label
        self.fid_indexs = fid_indexs
        self.date = date
        self.ts_code = ts_code
        self.name = name
        return 
    def __str__(self):
        return "TrainItem: fids: %s; label : %s" %(self.fids, self.label)
class TrainData():
    def __init__(self, instances, conf):
        self.instances = instances
        self.conf = conf 
        debug = self.conf.get("debug")
        self.validate_date = self.conf.get("validate_date", "")
        self.fid_whitelist =  set(debug.get("fid_whitelist") if debug.get("fid_whitelist") else [])    # 如果不为空，则只有这里的fid才会跑
        self.slot_whitelist =  set(debug.get("slot_whitelist") if debug.get("slot_whitelist") else [])    # 如果不为空，则只有这里的fid才会跑
        self.slot_blacklist =  set(debug.get("slot_blacklist") if debug.get("slot_blacklist") else [])    # 如果不为空，则只有这里的fid才会跑
        # 初始化每个fid的出现次数
        self.__init_fid2occu()
        # 给每个fid一个index，用于找embedding
        self.fid2index = {}   # 给每个fid一个index, 从0开始
        self.__init_fid2index_ins_filter()
        # 初始化训练数据
        self.__init_train_items()
        # Debug
        self.__debug()
        return
    def __debug(self):
        # if len(self.fid_whitelist) == 0 and len(self.slot_whitelist)== 0:
        #     return 
        self.fid2avg_label = {} 
        fid2label = {}
        for train_item in self.train_items: 
            label = train_item.label  
            for fid in train_item.fids:
                if fid not in fid2label:
                    fid2label[fid] = []
                fid2label[fid].append(label)
        # 按slot排序
        fids = list(fid2label)
        fids.sort(key = lambda f : f>>54)
        for fid in fids:
            # input("fid: %s slot: %s  ret: %s" %(fid, fid>>54, fid in self.fid_whitelist or fid >> 54 in self.slot_whitelist))
            if self._is_fid_in_whitelist(fid):
                labels = fid2label[fid] 
                avg_label = np.mean(labels) if len(labels) > 0 else 0
                self.fid2avg_label[fid] = avg_label
                raw_fea, extract_fea = self.fid2feature[fid]
                logging.info("[TrainData-Debug] (slot: %3d): %s(raw: %20s, feature: %10s) , ins_num: %d, label_mean: %.3f", fid>>54,
                                fid, raw_fea, extract_fea, len(labels), avg_label)
        logging.info("[TrainData-Debug] 所有可训练的slot: %s(%s)" %(len(self.all_slots), self.all_slots))
        return 

    def _is_fid_in_whitelist(self, fid):
        # fid是否在白名单那
        if fid>> 54 in self.slot_blacklist:
            return False   # 黑名单
        if len(self.fid_whitelist) == 0 and len(self.slot_whitelist)== 0:
            #  没有配置，则都算白名单
            return True 
        return fid in self.fid_whitelist or fid >> 54 in self.slot_whitelist
    
    def __get_label(self, ins):
        # 获取ins的label值
        # 错误则返回None
        def binarize(ins, args):
            #  label二值化
            label = 0
            threshold = args.get("threshold")
            key = args.get("key") 
            assert key in ins.label, "key %s not in label: %s" %(key, ins)
            label = 0  if ins.label[key] < threshold else 1
            return label 

        label_conf = self.conf.get("label")
        args = label_conf.get("args")
        try:
            label = None
            if label_conf.get("method") == "binarize":
                label = binarize(ins, args) 
        except:
            pass
        return label

    def __init_train_items(self):
        """
        """
        self.train_items = []
        self.validate_items = []
        ts_code2date_item = {} 
        for ins in self.valid_instances:

            fids = []
            for fc in ins.feature:
                fids.extend([fid for fid in  fc.fids if fid in self.fid2index])
            fid_indexs = [self.fid2index[fid] for fid in fids]
            label = self.__get_label(ins)
            if label is not None and ins.date < self.validate_date:
                self.train_items.append(TrainItem(fids, fid_indexs, label))
            else: 
                self.validate_items.append(TrainItem(fids, fid_indexs, 0, ts_code = ins.ts_code, date = ins.date, name = ins.name))  
        # 验证集
        assert len(self.validate_items) > 0, "验证集大小为0"
        logging.info("第一个TrainItem: %s" %(str(self.train_items[0])))
        logging.info("valid instance数: %s, 验证集: %s, 可训练数量: %s" %(len(self.valid_instances), 
                len(self.validate_items), len(self.train_items)))
        return 

    def __init_fid2occu(self):
        self.fid2occur = {}   # fid出现次数
        self.all_slots = set([])
        for ins in self.instances: 
            for fc in ins.feature:
                for fid in fc.fids:
                    self.fid2occur[fid] = self.fid2occur.get(fid, 0) + 1
                    self.all_slots.add(fid>>54)
        return 

    def __is_fid_neeed_filter(self, fid):
        """
          fid 过滤逻辑
        """
        min_fid_occur = self.conf.get("min_fid_occurrence", 0)
        if self.fid2occur[fid] < min_fid_occur:
            return True 
        # debug模式白名单才会通过
        return not self._is_fid_in_whitelist(fid)

    def __init_fid2index_ins_filter(self):
        """
           过滤instance: 即如果当前instance所有fid都被过滤掉，则整个instance过滤掉
        """
        self.fid2index = {}  # 每个fid对应一个Index，通过Index找embedding 
        self.index2fid = {}
        self.fid2feature = {}
        index = 0
        fid_filtered_set = set([])

        self.valid_instances = []
        for ins in self.instances: 
            # 是否所有fid都被过滤
            exist_valid_fid = False
            for fc in ins.feature:
                assert len(fc.fids) == 1, "每个feature column, 当前只支持1个fid"
                for i in range(len(fc.fids)):
                    fid = fc.fids[i]
                    raw_feature = ",".join(fc.raw_feature)
                    extracted_features = ",".join(fc.extracted_features)
                    if self.__is_fid_neeed_filter(fid):
                        if fid not in fid_filtered_set:
                            logging.info("FID filter: slot %3s fid %20s occu: %2s feature: %s raw: %s " %(fid >>54, fid, self.fid2occur[fid], raw_feature, extracted_features))
                            fid_filtered_set.add(fid)
                    else:
                        exist_valid_fid = True
                        if fid not in self.fid2index:
                            self.fid2index[fid] = index
                            self.index2fid[index] = fid
                            self.fid2feature[fid] = raw_feature, extracted_features
                            index += 1  
            if exist_valid_fid:
                self.valid_instances.append(ins)
        logging.info("总Instance数量: %s 过滤后的instance数(无fid):%s" %(len(self.instances), len(self.valid_instances))) 
        assert len(self.valid_instances) > 0
        logging.info("FID: 过滤后fid数: %s; fid出现次数至少:%s次，过滤FID数量: %s" %(index, self.conf.get("min_fid_occurrence", 0), len(fid_filtered_set)))
        return 
    
    def get_fid_num(self):
        """
          返回fid总数量, 用于初始化tensorflow
        """
        return len(self.fid2index) 

    def get_mini_batch(self, batch_size = 50):
        """
          从train_items随机采样batch_size个数据(这里可重复采样)
        """
        mini_batch = random.choices(self.train_items, k = batch_size)
        return mini_batch