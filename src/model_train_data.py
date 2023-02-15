
from common.utils import *
from common.stock_pb2 import *
import logging
import yaml
import random
import tensorflow.compat.v1 as tf
import logging
import numpy as np
import math
from collections import OrderedDict
from common.model_resource_manager import get_rm

class TrainItem():
    def __init__(self, fids, label, raw_label, name2dense, date = "", ts_code = "", name = ""):
        # 这里的fid为过滤过的fid
        self.fids = fids
        self.label = label
        self.raw_label = raw_label   # 原始label值
        self.date = date
        self.ts_code = ts_code
        self.name = name
        self.name2dense = name2dense
        return 
    def __str__(self):
        return "TrainItem: fids: %s; label : %s" %(self.fids, self.label)
    def get_slot_indexs(self, slot2index, fid2index):
        """ 
            目的: 返回每个slot对应的fid index. (保证一个slot最多一个fid)
            参数: slot2index: n个slot，映射到0~n-1
                 fid2index: m个slot, 映射到0~m-1
            返回: 长度为n的数组, 每个位置表示，当前slot，对应的fid_index
        """
        ret = [0] * len(slot2index)
        assert len(self.fids) == len(slot2index), "fids数量和slot不匹配: %s != %s %s vs %s" %(len(self.fids), len(slot2index), self.fids, slot2index)
        for fid in self.fids:
            fid_index = fid2index[fid]
            slot = fid >>54
            slot_index = slot2index[slot]
            ret[slot_index] = fid_index
        return ret
    
class TrainData():
    def __init__(self):
        self.instances = get_rm().instances
        self.conf = get_rm().conf.get("train_data") 
        debug = self.conf.get("debug")
        self.fid_whitelist =  set(debug.get("fid_whitelist") if debug.get("fid_whitelist") else [])    # 如果不为空，则只有这里的fid才会跑
        self.slot_whitelist =  set(debug.get("slot_whitelist") if debug.get("slot_whitelist") else [])    # 如果不为空，则只有这里的fid才会跑
        self.slot_blacklist =  set(debug.get("slot_blacklist") if debug.get("slot_blacklist") else [])    # 如果不为空，则只有这里的fid才会跑
        # 初始化每个fid的出现次数
        self.__init_fid2occu()
        # 给每个fid一个index，用于找embedding
        self.fid2index = {}   # 给每个fid一个index, 从0开始
        self.slots = []
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
        logging.info("[TrainData-Debug] 所有可训练的slot: %s(%s)" %(len(self.slots_set), self.slots_set))
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
        label_conf = self.conf.get("label")
        args = label_conf.get("args")
        key = args.get("key") 
        if key not in ins.label:
            return None, None
        raw_label = max(ins.label[key],ins.label["next_7d_close_price"])
        # if ins.label["next_7d_mean_price"] < -0.03:
        #    raw_label = ins.label["next_7d_close_price"]
        # if ins.label["next_3d_min_price"] < -0.1:
        #    raw_label = -0.1
        return raw_label, raw_label

    def __init_train_items(self):
        """
        """
        self.train_item_weights = []
        self.train_items = []
        self.validate_items = []
        for ins in self.valid_instances:
            fids = []
            name2dense = {}
            for fc in ins.feature:
                fids.extend([fid for fid in  fc.fids if fid in self.fid2index])
                if len(fc.dense) > 0:
                    name2dense[fc.name] = fc.dense
            label, raw_label = self.__get_label(ins)
            if label is not None and ins.date < get_rm().validate_date:
                train_item = TrainItem(fids, label, raw_label, name2dense, ts_code = ins.ts_code, date = ins.date)
                self.train_items.append(train_item)
                self.train_item_weights.append(self.__init_train_item_sample_weight(train_item))  # 训练样本权重
            else: 
                # 仍然写入label: 如果可用，则用户回测
                self.validate_items.append(TrainItem(fids, label, raw_label, name2dense, ts_code = ins.ts_code, date = ins.date, name = ins.name))  
        logging.info("train_item weights: %s" %(self.train_item_weights[:100]))
        # 验证集
        assert len(self.validate_items) > 0, "验证集大小为0"
        logging.info("第一个TrainItem: %s" %(str(self.train_items[0])))
        logging.info("valid instance数: %s, 验证集: %s, 可训练数量: %s" %(len(self.valid_instances), 
                len(self.validate_items), len(self.train_items)))
        return 

    def __init_fid2occu(self):
        self.fid2occur = {}   # fid出现次数
        self.slots_set = set([])
        for ins in self.instances: 
            for fc in ins.feature:
                for fid in fc.fids:
                    self.fid2occur[fid] = self.fid2occur.get(fid, 0) + 1
                    self.slots_set.add(fid>>54)
        return 

    def __is_fid_neeed_filter(self, fid):
        """
          fid 过滤逻辑
        """
        min_fid_occur = self.conf.get("min_fid_occurrence", 0)
        if self.fid2occur[fid] < min_fid_occur:
            raise Exception("fid: %s出现次数太低，尝试调整阈值 %s " %(fid, self.fid2occur[fid]))
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
        slot_set = set([])
        for ins in self.instances: 
            # 是否所有fid都被过滤
            exist_valid_fid = False
            for fc in ins.feature:
                assert len(fc.fids) <= 1, "每个feature column, 当前只支持1个fid %s" %(ins)
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
                            slot_set.add(fid>>54)
                            self.index2fid[index] = fid
                            self.fid2feature[fid] = raw_feature, extracted_features
                            index += 1  
            if exist_valid_fid:
                self.valid_instances.append(ins)
        self.slots = list(slot_set)
        self.slot2idx = {}                     # 每个slot对应一个index
        for i in range(len(self.slots)):
            self.slot2idx[self.slots[i]] = i
        logging.info("总Instance数量: %s 过滤后的instance数(无fid):%s" %(len(self.instances), len(self.valid_instances))) 
        assert len(self.valid_instances) > 0
        logging.info("FID: 过滤后fid数: %s; fid出现次数至少:%s次，过滤FID数量: %s" %(index, self.conf.get("min_fid_occurrence", 0), len(fid_filtered_set)))
        logging.info("总的Slots数量: %s (%s)" %(len(self.slots), self.slots))
        return 
    
    def get_fid_num(self):
        """
          返回fid总数量, 用于初始化tensorflow
        """
        return len(self.fid2index) 

    def __init_train_item_sample_weight(self, train_item):
        """
          每个训练样本的采样权重
        """
        return 1   # 权重都一样
        #
        # if raw_label_abs > 0.3:
        #     return 3
        # elif raw_label_abs > 0.15:
        #     return 2
        # else:
        #     return 1

    def get_mini_batch(self, batch_size = 50):
        """
          从train_items随机采样batch_size个数据(这里可重复采样)
        """
        if not hasattr(self, "batch_idx") :
            self.batch_idx = []
        if len(self.batch_idx) < batch_size:
            for i in range(len(self.train_items)):
                train_item = self.train_items[i]
                w = self.train_item_weights[i]
                self.batch_idx += [i] * w 
            random.shuffle(self.batch_idx)
            logging.info("refresh batch_idx: %s after shuffle: %s" %(len(self.batch_idx), self.batch_idx[:10]))
        assert len(self.batch_idx) >= batch_size, "所有权重还不够一次batch size"
        mini_batch = []
        for i in range(batch_size):
            idx = self.batch_idx.pop()
            mini_batch.append(self.train_items[idx])
        return mini_batch


        # , weights = self.train_item_weights,
        # mini_batch = random.choices(self.train_items, k = batch_size)
        # return mini_batch