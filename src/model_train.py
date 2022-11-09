# 模型训练
from common.utils import *
from common.stock_pb2 import *
import logging
import yaml
import random
import tensorflow as tf
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
    print('-'*100)
    print("总训练样本: %s" %(len(instances)))
    print("最后一个样本: %s" %(instances[-1]))
    print('-'*100)
    return instances

class TrainItem():
    def __init__(self, fids, fid_indexs, label):
        self.fids = []
        self.label = 0
        self.fid_indexs = fid_indexs
        return 

class TrainData():
    def __init__(self, instances, conf):
        self.instances = instances
        self.conf = conf 
        # 给每个fid一个index，用于找embedding
        self.__init_fid2index()
        # 初始化训练数据
        self.__init_train_items()
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
        return 

    def __init_train_items(self):
        self.train_items = []
        invalid_num = 0
        for ins in self.instances:
            try:
                label = self.__get_label(ins)
                fids = []
                for fc in ins.feature:
                    fids.extend(fc.fids)
                fid_indexs = [self.fid2index[fid] for fid in fids]
                self.train_items.append(TrainItem(fids, fid_indexs, label))
            except Exception as e:
                print("exp: %s" %(e))
                invalid_num += 1
        logging.error("文件中的instance数: %s, 异常数: %s, 可训练数量: %s" %(len(self.instances), invalid_num, len(self.train_items)))
        return 

    def __init_fid2index(self):
        self.fid2index = {}  # 每个fid对应一个Index，通过Index找embedding 
        self.index2fid = {}
        index = 0
        for ins in self.instances: 
            for fc in ins.feature:
                for fid in fc.fids:
                    if fid not in self.fid2index:
                        self.fid2index[fid] = index
                        self.index2fid[index] = fid
                        index += 1 
        
        print("-" * 100)
        print("不同总fid数: %s" %(index)) 
        print("-" * 100)
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

class Model: 
    def __init__(self, conf, fid_num):
        self.conf = conf
        self.fid_num = fid_num  

    def __init_sparse_embedding(self):
        bias_num = self.fid_num
        weight_initer = tf.truncated_normal_initializer(mean=0.0, stddev=0.01)
        self.sparse_bias = tf.get_variable(name="bias", dtype=tf.float32, shape=[bias_num], initializer=weight_initer)
        print("-"*100)
        print("bias num: %s %s" %(bias_num, self.sparse_bias))
        print("-"*100)
        return 
    
    def get_pred_and_loss(self, nn_out, label):
        """
          获取pred和loss
        """
        loss_type = self.conf.get("loss_type")
        if loss_type == 'cross_entropy':
            logit = nn_out # tf.reduce_sum(nn_out, axis=1)  
            pred = tf.sigmoid(logit, name = "pred")
            loss = tf.nn.sigmoid_cross_entropy_with_logits(labels=label, logits=logit)  
            loss = tf.reduce_sum(loss, name = "loss")
        else:
            raise Exception("unknown loss_type: %s" %(loss_type))
        return pred, loss

    def __build_dense_model(self):
        """
          建tensorflow图
        """
        # 输入placehold
        self.bias_fid_gate = tf.placeholder(tf.float32, [None, self.fid_num], name="bias_fid_gate")  # 长度为所有fid数量， 1表示有这个Fid， 0表示没有这个fid
        print("dense model: %s %s" %(self.sparse_bias, self.bias_fid_gate))
        bias_input = self.bias_fid_gate * self.sparse_bias                                 # 乘以开关
        
        # 过Dense nn, 得到pred和loss
        nn_out = tf.reduce_sum(bias_input, axis = 1)
        print("bias_input:%s nn_out: %s" %(bias_input, nn_out))

        self.label = tf.placeholder(tf.float32, [None], name = "label")
        self.pred, self.loss = self.get_pred_and_loss(nn_out, self.label)

        # optimizer
        op_conf = self.conf.get("optimizer")
        if op_conf.get("type") == "MomentumOptimizer" : 
            self.optimizer =tf.train.MomentumOptimizer(op_conf.get("learning_rate"), op_conf.get("momentum")).minimize(self.loss)            
        else:
            raise Exception("unknow optimizer")
        return 
    
    def __get_mini_batch_feed_dict(self, mini_batch):
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
    
    def train(self, train_data):
        # 初始化embedding : fid_index -> embedding的映射
        self.__init_sparse_embedding() 
        # 建图
        self.__build_dense_model()
        # 
        batch_size = self.conf.get("mini_batch").get("batch_size", 50) 
        epoch = self.conf.get("mini_batch").get("epoch", 1)         # 训练多少次
        # 开始训练
        sess = tf.Session()
        sess.run(tf.global_variables_initializer())
        for i in range(epoch):
            # 获取mini batch, 并转化为input
            mini_batch = train_data.get_mini_batch(batch_size)
            # 获取mini batch每个item的fid开关
            feed_dict = self.__get_mini_batch_feed_dict(mini_batch)

            # print("feed_dict: %s" %(feed_dict))
            # 开始训练
            _, pred, loss=sess.run([self.optimizer, self.pred, self.loss],
                    feed_dict = feed_dict)
            print("pred: %s; loss: %s" %(pred, loss))
            print("[train-epoch:%s]" %(i+1))
            #
        
        # 结果:
        bias_value = sess.run(self.sparse_bias)
        print("bias_value: %s" %(bias_value))
        for i in range(len(train_data.index2fid)):
            fid = train_data.index2fid[i]
            print("Fid: %s bias: %.3f" %(fid, bias_value))
        return 

if __name__ == "__main__":
    ## 载入yaml配置文件
    conf = yaml.safe_load(open("model_train.yaml", 'r') .read())
    files = conf.get("train_files") 
    # 载入instance
    instances = load_instance(files)
    # 处理instance
    train_data = TrainData(instances, conf.get("model_data")) 
    print(train_data.get_mini_batch())

    # 所有Fid的数量，用于模型初始化embedding/bias
    all_fid_num = train_data.get_fid_num()
    model = Model(conf.get("model"), all_fid_num)
    model.train(train_data)