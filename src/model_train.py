# 模型训练
from common.utils import *
from common.stock_pb2 import *
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
    def __init__(self, conf, train_data):
        self.conf = conf
        self.train_data = train_data
        self.fid_num = train_data.get_fid_num()
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
            loss = tf.reduce_sum(loss, name = "loss")
        else:
            raise Exception("unknown loss_type: %s" %(loss_type))
        return pred, loss
    
    def _build_dense_nn(self):
        # 建NN
        pass 
    def _get_model_feed_dict(self, mini_batch):
        """
          mini-batch为TrainItem数组, 转化为feed dict
        """
        pass
    def dense_tower(self, x, dims):
        # 过dnn，最后一层不会走relu
        for dim in dims[:-1]: 
            x = tf.layers.dense(x, dim, activation=tf.nn.relu)
        return tf.layers.dense(x, dim, activation=None)
    def _train(self):
        raise Exception("need override")
    def train(self):
        self._train()
    
class LRModel(Model): 
    """
      LR模型
    """
    def __init__(self, conf, train_data):
        super(LRModel, self).__init__(conf, train_data)
        return 
    def _init_sparse_embedding(self):
        bias_num = self.fid_num
        # weight_initer = tf.truncated_normal_initializer(mean=0.0, stddev=0.01)
        self.sparse_bias = tf.get_variable(name="bias", dtype=tf.float32, shape=[bias_num], initializer=tf.zeros_initializer())
        logging.info("bias num: %s %s" %(bias_num, self.sparse_bias)) 
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
        # 每个slot对应的fid下标
        self.slot_bias_fid_index = tf.placeholder(tf.int32, [None, slot_num], name="slot_bias_fid_index")  # 长度为所有fid数量， 1表示有这个Fid， 0表示没有这个fid
        # ins_fid_num = tf.reduce_sum(bias_fid_gate, axis = 1)                          # 每个instance有多少fid
        bias_input = tf.gather(self.sparse_bias, self.slot_bias_fid_index)                                # 乘以开关
        logging.info("[BuildDenseNN]dense model: %s fid_index: %s bias_input: %s" %(self.sparse_bias, 
                                self.slot_bias_fid_index, bias_input))
        
        # 过Dense nn, 得到pred和loss
        bias_sum = tf.reduce_sum(bias_input, axis = 1)
        logits = bias_sum + self.global_bias
        self.emit("logit/bias_sum", bias_sum)
        if isinstance(self.conf.get("bias_nn_dims"), list):
            dims = self.conf.get("bias_nn_dims")
            nn_out = tf.reduce_sum(self.dense_tower(bias_input, dims), axis = 1)
            self.emit("logit/bias_nn_out", nn_out)
            logits += nn_out
            self.losses.append(tf.reduce_sum(nn_out) * 1e-5)
            logging.info("[BuildDenseNN] towers: %s %s" %(dims, nn_out)) 
        self.emit("logit/sum", logits)
        logging.info("[BuildDenseNN]bias_input:%s logits: %s" %(bias_input, logits))

        return logits

    def _get_model_feed_dict(self, mini_batch):
        """
          将fid index映射为 0/1值, example:
            fid_index = [2, 4,5]
            返回: [0, 0, 1, 0, 1, 1, 0...0]
        """
        # 每个训练样本, 每个slot对应的fid index
        # slot_bias_fid_index
        fid_index = []
        # 每个训练样本的label
        label = []
        slot2index = self.train_data.slot2idx
        fid2index = self.train_data.fid2index
        for train_item in mini_batch:
            fid_index.append(train_item.get_slot_indexs(slot2index, fid2index))
            #label
            label.append(train_item.label)
        feed_dict = {
            self.learning_rate : self.conf.get("learning_rate"),
            self.slot_bias_fid_index:  fid_index,
            self.label : label
        }
        return feed_dict
    
    def _train(self):
        # 初始化embedding : fid_index -> embedding的映射
        self._init_sparse_embedding() 
        # 建图
        logits = self._build_dense_nn()

        # label和预估分
        self.label = tf.placeholder(tf.float32, [None], name = "label")
        self.pred, loss = self.get_pred_and_loss(logits, self.label)

        self.emit("pred", self.pred)
        self.emit("label", self.label)
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
                _, pred_val, loss_val, summary_val=sess.run([self.optimizer, self.pred, self.loss, self.all_summary],
                        feed_dict = feed_dict)
                self.writer.add_summary(summary_val, i)
                if i % 100 == 0:
                    label_avg = np.mean(feed_dict[self.label])
                    pred_avg = np.mean(pred_val)
                    logging.info("[train-epoch:%5s] loss: %.2f, label: %.2f pred: %.2f " %(i+1, 
                                        loss_val, label_avg, pred_avg))
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
            fid_val_pair = [(fid, fid2bias_val[fid]) for fid in fids]
            fid_val_pair.sort(key= lambda x : -x[1])
            return fid_val_pair[:k]
        items = self.train_data.validate_items[:100000]
        logging.info("开始预估股票: {}".format(len(items)).center(100, "="))
        # # tscode, date, TrainItem
        results = []   # ts_code, date, pred
        while len(items) > 0:
            batch_size = 500
            batch = items[:batch_size]
            items = items[batch_size:]
            feed_dict = self._get_model_feed_dict(batch)
            pred_val = self.sess.run(self.pred, feed_dict = feed_dict)
            for i in range(len(batch)):
                results.append({
                    "name" : batch[i].name,
                    "date" : batch[i].date,
                    "pred" : pred_val[i],
                    "item" : batch[i],
                    "label" : batch[i].label
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
            logging.info("[Top_%s] %s %s 概率: %.4f label_avg: %.4f 真实label: %s 正确率: %.2f" %(i, 
                        r["name"], r["date"], r["pred"], fids_label, r["label"], 1.0*correct_cnt/max(1, valid_cnt)))
            topk_fid_val = get_topk_val(fids, self.fid2bias_val)
            for fid, fid_bias in topk_fid_val:
                raw, feature = train_data.fid2feature[fid]
                logging.info("    [Top fid] slot: %3s fid: %19s, val: %.3f label: %.3f feature: %s, example_raw: %s" %(
                    fid>>54, fid, fid_bias, train_data.fid2avg_label.get(fid, 0), feature, raw))
        return 

if __name__ == "__main__":
    ## 载入yaml配置文件
    conf = yaml.safe_load(open("model_train.yaml", 'r') .read())
    files = conf.get("train_files")[:1]
    suffix = files[0].split(".")[-1] 
    logging.basicConfig(filename="%s.%s" %(conf.get("log_file"), suffix), format = '%(levelname)s %(asctime)s %(message)s', level=logging.DEBUG)
    # 载入instance
    logging.info("START")
    logging.info("conf: %s" %(conf)) 
    instances = read_instances(files)
    # 预处理instance: 处理label, 过滤fid等
    train_data = TrainData(instances, conf.get("train_data"))  

    # 所有Fid的数量，用于模型初始化embedding/bias
    model = LRModel(conf.get("model"), train_data)
    model.train()
    model.validate()
    print("执行: python parse_log.py  < ../log/model_train.log.20221122_1717 查看某一天具体正确率")