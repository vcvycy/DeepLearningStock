
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
    logging.info("第一个Instance: %s" %(instances[0])) 
    logging.info("总训练样本: %s" %(len(instances)))
    return instances

class TrainItem():
    def __init__(self, fids, fid_indexs, label):
        # 这里的fid为过滤过的fid
        self.fids = fids
        self.label = label
        self.fid_indexs = fid_indexs
        return 
    def __str__(self):
        return "TrainItem: fids: %s; label : %s" %(self.fids, self.label)
class TrainData():
    def __init__(self, instances, conf):
        self.instances = instances
        self.conf = conf 
        debug = self.conf.get("debug")
        self.fid_whitelist =  set(debug.get("fid_whitelist") if debug.get("fid_whitelist") else [])    # 如果不为空，则只有这里的fid才会跑
        self.slot_whitelist =  set(debug.get("slot_whitelist") if debug.get("slot_whitelist") else [])    # 如果不为空，则只有这里的fid才会跑
        # 初始化每个fid的出现次数
        self.__init_fid2occu()
        # 给每个fid一个index，用于找embedding
        self.__init_fid2index_ins_filter()
        # 初始化训练数据
        self.__init_train_items()
        # Debug
        self.__debug()
        return
    def __debug(self):
        # if len(self.fid_whitelist) == 0 and len(self.slot_whitelist)== 0:
        #     return 
        print("whitelist: %s %s" %(self.fid_whitelist, self.slot_whitelist))
        fid2label = {}
        for train_item in self.train_items: 
            label = train_item.label  
            for fid in train_item.fids:
                if fid not in fid2label:
                    fid2label[fid] = []
                fid2label[fid].append(label)
        
        for fid in fid2label:
            # input("fid: %s slot: %s  ret: %s" %(fid, fid>>54, fid in self.fid_whitelist or fid >> 54 in self.slot_whitelist))
            if self._is_fid_in_whitelist(fid):
                labels = fid2label[fid] 
                logging.info("[TrainData-Debug] fid(slot: %3d): %s(raw_feature: %20s), label数量: %d, label_mean: %.3f", fid,
                                fid>>54, self.fid2feature[fid], len(labels), np.mean(labels))
        logging.info("[TrainData-Debug] 所有可训练的slot: %s(%s)" %(len(self.all_slots), self.all_slots))
        input("[Debug End]press any key to continue...")
        return 

    def _is_fid_in_whitelist(self, fid):
        # fid是否在白名单那
        if len(self.fid_whitelist) == 0 and len(self.slot_whitelist)== 0:
            #  没有配置，则都算白名单
            return True 
        return fid in self.fid_whitelist or fid >> 54 in self.slot_whitelist
    
    def __get_label(self, ins):
        # 获取ins的label值
        # 错误抛出异常
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
        if label_conf.get("method") == "binarize":
            label = binarize(ins, args)
        else:
            raise Exception("method unknown")
        return label

    def __init_train_items(self):
        self.train_items = []
        invalid_num = 0
        for ins in self.valid_instances:
            try:
                label = self.__get_label(ins)
                fids = []
                for fc in ins.feature:
                    fids.extend([fid for fid in  fc.fids if fid in self.fid2index])
                fid_indexs = [self.fid2index[fid] for fid in fids]
                self.train_items.append(TrainItem(fids, fid_indexs, label))
            except Exception as e:
                print("exp: %s" %(e))
                invalid_num += 1
        logging.info("第一个TrainItem: %s" %(str(self.train_items[0])))
        logging.info("valid instance数: %s, 异常数: %s, 可训练数量: %s" %(len(self.valid_instances), invalid_num, len(self.train_items)))
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
        self.fid2index = {}  # 每个fid对应一个Index，通过Index找embedding 
        self.index2fid = {}
        self.fid2feature = {}
        index = 0
        fid_filtered_num = 0

        self.valid_instances = []
        for ins in self.instances: 
            # 是否所有fid都被过滤
            exist_valid_fid = False
            for fc in ins.feature:
                assert len(fc.fids) == 1, "每个feature column, 当前只支持1个fid"
                for i in range(len(fc.fids)):
                    fid = fc.fids[i]
                    if self.__is_fid_neeed_filter(fid):
                        fid_filtered_num +=1
                    else:
                        exist_valid_fid = True
                        raw_feature = str(fc.raw_feature)
                        if fid not in self.fid2index:
                            self.fid2index[fid] = index
                            self.index2fid[index] = fid
                            self.fid2feature[fid] = raw_feature 
                            index += 1  
            if exist_valid_fid:
                self.valid_instances.append(ins)
        logging.info("总Instance数量: %s 过滤后的instance数(无fid):%s" %(len(self.instances), len(self.valid_instances))) 
        assert len(self.valid_instances) > 0
        logging.info("FID: 过滤后fid数: %s; fid出现次数至少:%s次，过滤FID数量: %s" %(index, self.conf.get("min_fid_occurrence", 0), fid_filtered_num))
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