# 模型训练
from common.utils import *
from common.stock_pb2 import *
from common.model_resource_manager import get_rm, init_singleton_rm
import logging
import yaml
import random
import tensorflow as tf
import logging
import math
import numpy as np
from model_train_data import *
import time
# time.sleep(3600*2)

class Model():
    def __init__(self):
        self.conf = get_rm().conf.get("model")
        self.train_data = TrainData()
        self.fid_num = self.train_data.get_fid_num()
        self.losses = []
        self.sess = tf.Session()
        self.writer = tf.summary.FileWriter("./tboard/", self.sess.graph)  
    #     self.init_fid2index()
    #     return 
    # def init_fid2index(self):
    #     """
    #       给每个fid一个index
    #     """
    #     cur_index = 0
    #     self.fid2index = {}
    #     for train_item in self.train_data.train_items:
    #         for fid in train_item.fids:
    #             if fid not in self.fid2index:
    #                 self.fid2index[fid] = cur_index
    #                 cur_index += 1
    #     return 
    def emit(self, name, tensor):
        tf.summary.scalar(name, tf.reduce_mean(tensor))
        tf.summary.histogram(name, tensor)
        return 
    def _get_optimizer(self):
        # optimizer
        self.learning_rate=tf.placeholder(tf.float32,name="learning_rate")
        op_conf = self.conf.get("optimizer")
        if op_conf.get("type") == "MomentumOptimizer" : 
            optimizer =tf.train.MomentumOptimizer(self.learning_rate, op_conf.get("momentum")).minimize(self.loss)  
        elif op_conf.get("type") == "AdagradOptimizer":
            optimizer =tf.train.AdagradOptimizer(self.learning_rate).minimize(self.loss)  
        elif op_conf.get("type") == "GradientDescentOptimizer":
            optimizer =tf.train.GradientDescentOptimizer(self.learning_rate).minimize(self.loss)  
        else:
            raise Exception("unknow optimizer") 
        return optimizer 
    
    def get_pred_and_loss(self, logits, label):
        """
          获取pred和loss
        """
        loss_type = self.conf.get("loss_type")
        if loss_type == 'cross_entropy':
            pred = tf.sigmoid(logits, name = "pred")
            loss = tf.nn.sigmoid_cross_entropy_with_logits(labels=label, logits=logits)  
        # elif loss_type == "mse":
        #     pred = logits
        #     loss = (label - pred) * (label - pred)
        #     print("MSE: %s" %(loss))
        elif loss_type == "mse":
            pred = logits
            loss = (pred - label) * (pred -label)
        else:
            raise Exception("unknown loss_type: %s" %(loss_type))
        self.get_certrain_prob()
        # loss *= self.certainly
        loss = tf.reduce_sum(loss, name = "loss")
        return pred, loss
    
    def _build_dense_nn(self):
        # 建NN
        pass 
    def _get_model_feed_dict(self, mini_batch, training = True):
        """
          mini-batch为TrainItem数组, 转化为feed dict
          默认为training，即包含label
        """
        pass
    
    def _get_variable(self, name, shape,initializer = tf.keras.initializers.he_normal()):\
        return tf.get_variable(name,
                            shape=shape,
                            initializer=initializer)
    def fc(self,x,num,name):
        x_num=x.get_shape()[1].value
        weight_shape=[x_num,num]
        bias_shape  =[num]
        weight=self._get_variable("%s/weight" %(name),shape=weight_shape)
        bias  =self._get_variable("%s/bias" %(name),shape=bias_shape)
        self.emit("%s/weight" %(name), weight)
        self.emit("%s/bias" %(name), bias)
        y=tf.add(tf.matmul(x,weight),bias,name=name)
        return y 
    # def dense_tower(self, x, dims):
    #     # 过dnn，最后一层不会走relu
    #     l1_reg = None
    #     for dim in dims[:-1]: 
    #         # x = tf.nn.dropout(x, 0.1)
    #         x = tf.layers.dense(x, dim, activation=tf.nn.relu, kernel_regularizer= l1_reg)
    #     return tf.layers.dense(x, dims[-1], activation=None, kernel_regularizer= l1_reg)
    def dense_tower(self, x, dims, name ):
        layer = 1
        for dim in dims[:-1]: 
            x = self.fc(x, dim, "dense_tower/%s/%s" %(name, layer))
            x = tf.nn.relu(x)
            self.emit("dense_tower/%s/%s/zero_fraction" %(name, layer), tf.nn.zero_fraction(x))
            layer += 1
        return self.fc(x, dims[-1], "dense_tower/%s/%s" %(name, layer))
    def _train(self):
        raise Exception("need override")
    def train(self):
        self._train()
    
class LRModel(Model): 
    """
      LR模型
    """
    def __init__(self):
        super(LRModel, self).__init__()
        return 
    
    def get_slot_concat_embedding(self, name, gather = True):
        weight_initer = tf.truncated_normal_initializer(mean=0.0, stddev=0.01)
        all_fid_embed =  tf.get_variable(name=name, dtype=tf.float32, shape=[self.fid_num], initializer=weight_initer)
        self.emit("all_fid_embed/%s" %(name), all_fid_embed)
        if gather:
            slot_embed = tf.gather(all_fid_embed, self.slot_bias_fid_index) 
            self.emit("slot_embedding/%s" %(name), slot_embed)
            return slot_embed
        else:
            return all_fid_embed
        
    def _init_sparse_embedding(self):
        bias_num = self.fid_num
        # weight_initer = tf.truncated_normal_initializer(mean=0.0, stddev=0.01)
        self.sparse_bias = self.get_slot_concat_embedding("bias", gather = False) # tf.get_variable(name="bias", dtype=tf.float32, shape=[bias_num], initializer=tf.zeros_initializer())
        self.certain_bias =  self.get_slot_concat_embedding("certain_bias") # tf.get_variable(name="certain_bias", dtype=tf.float32, shape=[bias_num], initializer=tf.zeros_initializer())
        logging.info("bias num: %s %s" %(bias_num, self.sparse_bias)) 
        return 

    def get_certrain_prob(self):
        # 每个样本的确定性, 为0.5 ~1.5对loss加权， 确定性高的loss大，低的loss小
        input = self.certain_bias
        logits = tf.reduce_sum(input, axis = 1)
        self.emit("certainly/logits", logits)
        certainly_raw= tf.sigmoid(logits) + 0.2
        self.emit("certainly/raw_val", certainly_raw)
        certainly = certainly_raw/ tf.reduce_mean(certainly_raw)
        print("certainly: %s" %(certainly))
        self.emit("certainly/norm_val", certainly)
        # 总体确定性平均值应该为
        self.certainly_raw = certainly_raw
        self.certainly = certainly
        # loss = tf.abs(tf.reduce_mean(certainly) - 1)
        # self.emit("certainly/loss", loss)
        # self.losses.append(loss)
        return 
        
    def _build_dense_nn(self):
        """
          建tensorflow: 这里为LR模型
        """
        slot_num = len(self.train_data.slots)
        # 输入placehold
        if self.conf.get("global_bias") == True:
            self.global_bias = tf.get_variable(name="global_bias", dtype=tf.float32, shape=[1], initializer=tf.zeros_initializer())
        else:
            self.global_bias = tf.constant(0, dtype=tf.float32)
        # ins_fid_num = tf.reduce_sum(bias_fid_gate, axis = 1)                          # 每个instance有多少fid
        bias_input = tf.gather(self.sparse_bias, self.slot_bias_fid_index)                                # 乘以开关
        logging.info("[BuildDenseNN]dense model: %s fid_index: %s bias_input: %s" %(self.sparse_bias, 
                                self.slot_bias_fid_index, bias_input))
        
        logits = 0
        # 过去30天走势dense图
        if self.conf.get("dense_30d"):
            self.last_30d_close = tf.placeholder(tf.float32, [None, 30], name="last_30d_close")  # 长度为所有fid数量， 1表示有这个Fid， 0表示没有这个fid
            self.emit("last_30d_close", self.last_30d_close)
            last_30d_nn_out = tf.reduce_sum(self.dense_tower(self.last_30d_close, [8, 1], name="dense_30d"), axis = 1)
            self.emit("logits/last_30d_out", last_30d_nn_out)
            logits += last_30d_nn_out
        
        # 过Dense nn, 得到pred和loss
        if self.conf.get("bias_attention"):
            bias_attention = tf.nn.sigmoid(self.dense_tower(bias_input, [16, slot_num], name="bias_attn"))
            self.emit("bias_attention", bias_attention)
            bias_input_attn = bias_input * bias_attention
            bias_sum = tf.reduce_mean(bias_input_attn, axis = 1)
            # 每个slot监控
            attn_transpose = tf.transpose(bias_attention)
            slot2index = self.train_data.slot2idx
            index2slot = {slot2index[slot] : slot for slot in slot2index}
            for idx in index2slot:
                slot = index2slot[idx]
                self.emit("attention/slot_%s_idx_%s" %(slot, idx), attn_transpose[idx])
        else:
            bias_sum = tf.reduce_mean(bias_input, axis = 1)
        logits += bias_sum + self.global_bias
        self.emit("logit/bias_sum", bias_sum)
        if isinstance(self.conf.get("bias_nn_dims"), list):
            dims = self.conf.get("bias_nn_dims")
            nn_out = tf.reduce_sum(self.dense_tower(bias_input, dims, name="bias_nn"), axis = 1)
            self.emit("logit/bias_nn_out", nn_out)
            logits += nn_out
            # self.losses.append(tf.reduce_sum(nn_out) * 1e-5)
            logging.info("[BuildDenseNN] towers: %s %s" %(dims, nn_out)) 
        self.emit("logit/sum", logits)
        logging.info("[BuildDenseNN]bias_input:%s logits: %s" %(bias_input, logits))

        return logits

    def _get_model_feed_dict(self, mini_batch, training = True):
        """
          将fid index映射为 0/1值, example:
            fid_index = [2, 4,5]
            返回: [0, 0, 1, 0, 1, 1, 0...0]
        """
        # 每个训练样本, 每个slot对应的fid index
        # slot_bias_fid_index
        fid_index = []
        slot2index = self.train_data.slot2idx
        fid2index = self.train_data.fid2index
        # last_30d_close = []
        for train_item in mini_batch:
            fid_index.append(train_item.get_slot_indexs(slot2index, fid2index))
            #label
            # last_30d_close.append(train_item.name2dense["last_30d_close"])
        feed_dict = {
            self.learning_rate : self.conf.get("learning_rate"),
            self.slot_bias_fid_index:  fid_index
            # self.last_30d_close :last_30d_close
        }
        if training: # label 只有训练的时候才要传
            raw_label = [] 
            for train_item in mini_batch:
                date2thre = get_rm().date2thre
                # print("rawlabel %s thre: %s" %(train_item.raw_label, date2thre[train_item.date]))
                thre = 0# max(-0.03, date2thre[train_item.date])
                raw_label.append(train_item.raw_label - thre)
                # raw_label.append(train_item.raw_label)
            feed_dict[self.raw_label] = raw_label
        return feed_dict
    
    def _train(self):
        # 初始化embedding : fid_index -> embedding的映射
        # 每个slot对应的fid下标
        slot_num = len(self.train_data.slots)
        self.slot_bias_fid_index = tf.placeholder(tf.int32, [None, slot_num], name="slot_bias_fid_index")  # 长度为所有fid数量， 1表示有这个Fid， 0表示没有这个fid
        self._init_sparse_embedding() 
        # 建图
        logits = self._build_dense_nn()

        # label和预估分
        self.raw_label = tf.placeholder(tf.float32, [None], name = "raw_label") 
        if self.conf.get("label").get("binarized", None) is not None:
            threshold = self.conf.get("label").get("binarized", None)
            logging.info("label 二值化: %s" %(threshold))
            self.label = tf.where(self.raw_label > threshold, tf.ones_like(self.raw_label), tf.zeros_like(self.raw_label), name = "label")
        else:
            self.label = self.raw_label
        self.pred, loss = self.get_pred_and_loss(logits, self.label)

        self.emit("pred", self.pred)
        self.emit("label", self.label)
        self.emit("raw_label", self.raw_label)
        self.losses.append(loss)
        self.loss = tf.add_n(self.losses)

        self.emit("loss", self.loss)
        # optimizer初始化
        self.optimizer = self._get_optimizer()

        # 训练参数
        train_data = self.train_data
        batch_size = self.conf.get("mini_batch").get("batch_size", 50) 
        epoch = self.conf.get("mini_batch").get("epoch", 1)         # 训练多少次
        # 开始训练

        logging.info("[Train] start to train, batch size: %s,  epoch: %s" %(batch_size, epoch))
        sess = self.sess
        sess.run(tf.global_variables_initializer())
        self.all_summary = tf.summary.merge_all()
        self.global_step = 0
        for i in range(epoch):
            try:
                self.global_step = i
                # 获取mini batch, 并转化为input
                mini_batch = train_data.get_mini_batch(batch_size)
                # 获取mini batch每个item的fid开关
                feed_dict = self._get_model_feed_dict(mini_batch)

                # 开始训练
                _, pred_val, loss_val, label_val, summary_val=sess.run([self.optimizer, self.pred, self.loss, self.label, self.all_summary],
                        feed_dict = feed_dict)
                self.writer.add_summary(summary_val, i)
                if i % 100 == 0:
                    label_avg = np.mean(label_val)
                    pred_avg = np.mean(pred_val)
                    logging.info("[train-epoch:%5s] loss: %.2f, label: %.2f pred: %.2f batch_size: %s" %(i+1, 
                                        loss_val, label_avg, pred_avg, len(mini_batch)))
            except KeyboardInterrupt:
                logging.info("手动退出训练过程")
                break
        # 结果: 输出Fid对应的值
        bias_value, global_bias_val, bias_value_with_gbias = sess.run([self.sparse_bias, 
                           self.global_bias, tf.sigmoid(self.sparse_bias + self.global_bias)])
        logging.info("bias_value(原始值): %s ; global_bias: %s" %(bias_value, global_bias_val))
        # 每个fid的bias值
        self.fid2bias_val = {}
        features = []
        for fid in train_data.fid2avg_label:
            raw, feature = train_data.fid2feature[fid]
            fid_index = train_data.fid2index[fid]
            self.fid2bias_val[fid] = bias_value[fid_index]
            features.append((fid>>54, fid, fid_index, feature, train_data.fid2occur[fid], raw)) 

        bias_label_diff = 0
        features.sort(key= lambda x : "%s-%s" %(x[0], x[3])) # 按slot排序 
        # fid2avg_label: 没有fid2index的一些数据，原因: fid2avg_label只有训练集的fid，而fid2index还包含验证集的fid
        for slot, fid, index, feature, occur, raw in features: 
            logging.info("[slot: %s %s] [次数:%7s] [bias_with_g_bias: %.3f vs  %.3f(label)]  (feature: %7s raw %s)" %(slot, fid, 
                    occur, bias_value_with_gbias[index], train_data.fid2avg_label.get(fid, 0), feature, raw))
            bias_label_diff += math.fabs(train_data.fid2avg_label[fid] - bias_value_with_gbias[index])
        logging.info("sum(bias-label) = %s" %(bias_label_diff))
        return 

    def validate(self):
        """
          模型验证: 输出最有前途的股票
        """
        def get_topk_val(fids, fid2bias_val, k = 10):
            # 获取fid最高的K个
            fid_val_pair = [(fid, fid2bias_val.get(fid, -1)) for fid in fids]
            fid_val_pair.sort(key= lambda x : -x[1])
            return fid_val_pair[:k]
        train_data = self.train_data
        items = train_data.validate_items
        logging.info("开始预估股票: {}".format(len(items)).center(100, "="))
        # # tscode, date, TrainItem
        results = []   # ts_code, date, pred
        while len(items) > 0:
            batch_size = 500
            batch = items[:batch_size]
            items = items[batch_size:]
            feed_dict = self._get_model_feed_dict(batch, training = False)
            pred_val, certainly_val = self.sess.run([self.pred, self.certainly_raw], feed_dict = feed_dict)
            for i in range(len(batch)):
                results.append({
                    "name" : batch[i].name,
                    "date" : batch[i].date,
                    "pred" : pred_val[i],
                    "item" : batch[i],
                    "label" : batch[i].label,
                    "certainly" : certainly_val[i],
                    "raw_label" : batch[i].raw_label if batch[i].raw_label is not None else 999
                })
        #
        results.sort(key = lambda x : -x["pred"])
        correct_cnt = 0
        valid_cnt = 0
        for i in range(len(results)):
            r = results[i]
            # 真实label
            if r["label"] is not None:
                valid_cnt += 1
                if  r["label"]> 0:
                    correct_cnt += 1 
            # 获取topk fid
            fids = r["item"].fids
            fids_label = np.mean([train_data.fid2avg_label.get(fid, 0) for fid in fids])
            logging.info("[Top_%s] %s %s 概率: %.4f fid_label_avg: %.4f label: %s raw_label: %.3f 确定性: %.3f 正确率: %.2f" %(i, 
                        r["name"], r["date"], r["pred"], fids_label, r["label"], r["raw_label"], r["certainly"], 1.0*correct_cnt/max(1, valid_cnt)))
            if i >= 1000:
                continue
            topk_fid_val = get_topk_val(fids, self.fid2bias_val)
            for fid, fid_bias in topk_fid_val:
                raw, feature = train_data.fid2feature[fid]
                logging.info("    [Top fid] slot: %3s fid: %19s, val: %.3f label: %.3f feature: %s, example_raw: %s" %(
                    fid>>54, fid, fid_bias, train_data.fid2avg_label.get(fid, 0), feature, raw))
        return 

if __name__ == "__main__":
    ## 载入yaml配置文件
    init_singleton_rm("model_train.yaml")
    # 所有Fid的数量，用于模型初始化embedding/bias
    model = LRModel()
    model.train()
    model.validate()
    logging.info("END")
    print(" python test_parse_log.py  < %s" %(get_rm().log_file))