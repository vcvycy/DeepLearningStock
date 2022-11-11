# 模型训练
from common.utils import *
from common.stock_pb2 import *
import logging
import yaml
import random
import tensorflow as tf
import logging
import numpy as np
def load_instance(files):
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
        self.__init_fid2index()
        # 初始化训练数据
        self.__init_train_items()
        # Debug
        self.__debug()
        return
    def __debug(self):
        if len(self.fid_whitelist) and len(self.slot_whitelist)== 0:
            return 
        fid2label = {}
        for train_item in self.train_items: 
            label = train_item.label  
            for fid in train_item.fids:
                if fid not in fid2label:
                    fid2label[fid] = []
                fid2label[fid].append(label)
        
        for fid in fid2label:
            if fid in self.fid_whitelist or fid >> 54 in self.slot_whitelist: 
                labels = fid2label[fid] 
                logging.info("[TrainData-Debug] fid: %s(%20s), label数量: %.3f, label_mean: %.3f", fid, self.fid2feature[fid], len(labels), np.mean(labels))
        input("[Debug End]press any key to continue...")
        return 

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
        for ins in self.instances:
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
        logging.info("文件中的instance数: %s, 异常数: %s, 可训练数量: %s" %(len(self.instances), invalid_num, len(self.train_items)))
        return 

    def __init_fid2occu(self):
        self.fid2occur = {}   # fid出现次数
        for ins in self.instances: 
            for fc in ins.feature:
                for fid in fc.fids:
                    self.fid2occur[fid] = self.fid2occur.get(fid, 0) + 1
        return 

    def __is_fid_neeed_filter(self, fid):
        """
          fid 过滤逻辑
        """
        min_fid_occur = self.conf.get("min_fid_occurrence", 0)
        if self.fid2occur[fid] < min_fid_occur:
            return True 
        # debug模式白名单才会通过
        if len(self.fid_whitelist) > 0 and fid not in self.fid_whitelist:
            return True
        if len(self.slot_whitelist) > 0 and fid >> 54 not in self.slot_whitelist:
            return True
        return False

    def __init_fid2index(self):
        self.fid2index = {}  # 每个fid对应一个Index，通过Index找embedding 
        self.index2fid = {}
        self.fid2feature = {}
        index = 0
        fid_filtered_num = 0
        for ins in self.instances: 
            for fc in ins.feature:
                for i in range(len(fc.fids)):
                    fid = fc.fids[i]
                    if self.__is_fid_neeed_filter(fid):
                        fid_filtered_num +=1
                    else:
                        raw_feature = fc.raw_feature[i]
                        if fid not in self.fid2index:
                            self.fid2index[fid] = index
                            self.index2fid[index] = fid
                            self.fid2feature[fid] = raw_feature 
                            index += 1  
        
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

class Model():
    def __init__(self, conf, train_data):
        self.conf = conf
        self.train_data = train_data
        self.fid_num = train_data.get_fid_num()
        return 
    def _get_optimizer(self):
        # optimizer
        op_conf = self.conf.get("optimizer")
        if op_conf.get("type") == "MomentumOptimizer" : 
            optimizer =tf.train.MomentumOptimizer(op_conf.get("learning_rate"), op_conf.get("momentum")).minimize(self.loss)  
        elif op_conf.get("type") == "AdagradOptimizer":
            optimizer =tf.train.AdagradOptimizer(op_conf.get("learning_rate")).minimize(self.loss)  
        elif op_conf.get("type") == "GradientDescentOptimizer":
            optimizer =tf.train.GradientDescentOptimizer(op_conf.get("learning_rate")).minimize(self.loss)  
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
    def _pretrain(self):
        return 
    def train(self):
        self._pretrain()
        pass 
class LRModel(Model): 
    """
      LR模型
    """
    def __init__(self, conf, train_data):
        super(LRModel, self).__init__(conf, train_data)
        return 
    def _init_sparse_embedding(self):
        bias_num = self.fid_num
        weight_initer = tf.truncated_normal_initializer(mean=0.0, stddev=0.01)
        self.sparse_bias = tf.get_variable(name="bias", dtype=tf.float32, shape=[bias_num], initializer=weight_initer)
        logging.info("bias num: %s %s" %(bias_num, self.sparse_bias)) 
        return 
    

    def _build_dense_nn(self):
        """
          建tensorflow: 这里为LR模型
        """
        # 输入placehold
        if self.conf.get("global_bias") == True:
            self.global_bias = tf.get_variable(name="global_bias", dtype=tf.float32, shape=[1], initializer=tf.zeros_initializer())
        else:
            self.global_bias = tf.constant(0, dtype=tf.float32)
        bias_fid_gate = tf.placeholder(tf.float32, [None, self.fid_num], name="bias_fid_gate")  # 长度为所有fid数量， 1表示有这个Fid， 0表示没有这个fid
        logging.info("dense model: %s %s" %(self.sparse_bias, bias_fid_gate))
        bias_input = bias_fid_gate * self.sparse_bias                                 # 乘以开关
        
        # 过Dense nn, 得到pred和loss
        logits = tf.reduce_sum(bias_input, axis = 1) + self.global_bias
        logging.info("bias_input:%s logits: %s" %(bias_input, logits))

        return bias_fid_gate, logits

    def _get_model_feed_dict(self, mini_batch):
        """
          将fid index映射为 0/1值, example:
            fid_index = [2, 4,5]
            返回: [0, 0, 1, 0, 1, 1, 0...0]
        """
        # 每个训练样本，有多少Fid开着
        bias_fid_gate = []
        # 每个训练样本的label
        label = []
        
        for train_item in mini_batch:
            fid_gate = [0] * self.fid_num
            for i in train_item.fid_indexs:
                fid_gate[i] = 1
            bias_fid_gate.append(fid_gate)
            #label
            label.append(train_item.label)
        feed_dict = {
            self.bias_fid_gate:  bias_fid_gate,
            self.label : label
        }
        return feed_dict
    
    def train(self):
        # 初始化embedding : fid_index -> embedding的映射
        self._init_sparse_embedding() 
        # 建图
        self.bias_fid_gate, logits = self._build_dense_nn()

        # label和预估分
        self.label = tf.placeholder(tf.float32, [None], name = "label")
        self.pred, self.loss = self.get_pred_and_loss(logits, self.label)

        # optimizer初始化
        self.optimizer = self._get_optimizer()

        # 训练参数
        self.train_data = train_data
        batch_size = self.conf.get("mini_batch").get("batch_size", 50) 
        epoch = self.conf.get("mini_batch").get("epoch", 1)         # 训练多少次
        # 开始训练

        logging.info("[Train] start to train, batch size: %s,  epoch: %s" %(batch_size, epoch))
        self.sess = sess = tf.Session()
        sess.run(tf.global_variables_initializer())
        for i in range(epoch):
            # 获取mini batch, 并转化为input
            mini_batch = train_data.get_mini_batch(batch_size)
            # 获取mini batch每个item的fid开关
            feed_dict = self._get_model_feed_dict(mini_batch)

            # 开始训练
            _, pred_val, loss_val=sess.run([self.optimizer, self.pred, self.loss],
                    feed_dict = feed_dict)
            if i % 100 == 0:
                logging.info("[train-epoch:%s] loss: %s, pred:%s" %(i+1, loss_val, pred_val[:5]))
            #
        
        # 结果: 输出Fid对应的值
        bias_value, bias_value_with_gbias = sess.run([tf.sigmoid(self.sparse_bias), tf.sigmoid(self.sparse_bias + self.global_bias)])
        logging.info("bias_value: %s" %(bias_value))
        features = []
        for fid in train_data.fid2index:
            feature = train_data.fid2feature[fid]
            features.append((fid>>54, fid, train_data.fid2index[fid], feature, train_data.fid2occur[fid])) 

        features.sort(key= lambda x : "%s-%s" %(x[0], x[3])) # 按slot排序
        global_bias_val = sess.run(self.global_bias)
        logging.info("global_bais: %s" %(global_bias_val))
        for slot, fid, index, feature, occur in features: 
            raw_feature = train_data.fid2feature[fid]
            logging.info("[slot: %s %s %20s] [次数: %5s] [bias: %.3f]  (%s)" %(slot, fid, 
                    raw_feature,  occur, bias_value_with_gbias[index], feature))
        return 

if __name__ == "__main__":
    ## 载入yaml配置文件
    conf = yaml.safe_load(open("model_train.yaml", 'r') .read())
    files = conf.get("train_files") 
    logging.basicConfig(filename=conf.get("log_file"), format = '%(levelname)s %(asctime)s %(message)s', level=logging.DEBUG)
    # 载入instance
    logging.info("START")
    logging.info("conf: %s" %(conf)) 
    instances = load_instance(files)
    # 预处理instance: 处理label, 过滤fid等
    train_data = TrainData(instances, conf.get("train_data"))  

    # 所有Fid的数量，用于模型初始化embedding/bias
    model = LRModel(conf.get("model"), train_data)
    model.train()