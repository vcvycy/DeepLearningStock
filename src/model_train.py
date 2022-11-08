# 模型训练
from common.utils import *
from common.stock_pb2 import *
import logging
import yaml
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
    def __init__(self, fids, label):
        self.fids = []
        self.label = 0
        return 
    def add_fids(fids):
        self.fids.extend(fids)

class TrainData():
    def __init__(self, instances, conf):
        self.instances = instances
        self.conf = conf 
        # 初始化训练数据
        self.init_train_data()
        # 给每个fid一个index，用于找embedding
        # self.init_fid2index()
        return
    
    def get_label(self, ins):
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

    def init_train_data(self):
        self.train_data = []
        invalid_num = 0
        for ins in self.instances:
            try:
                label = self.get_label(ins)
                fids = []
                for fc in ins.feature:
                    fids.extend(fc.fids)
                self.train_data.append(TrainItem(fids, label))
            except Exception as e:
                print("exp: %s" %(e))
                invalid_num += 1
        logging.error("文件中的instance数: %s, 异常数: %s, 可训练数量: %s" %(len(self.instances), invalid_num, len(self.train_data)))
        return 

    def init_fid2index(self):
        self.fid2index = {}  # 每个fid对应一个Index，通过Index找embedding 
        index = 0
        for ins in self.instances: 
            for fc in ins.feature:
                for fid in fc.fids:
                    if fid not in fid2index:
                        self.fid2index[fid] = index
                        index += 1 
        
        print("-" * 100)
        print("不同总fid数: %s" %(index))
        print(self.fid2index)
        print("-" * 100)
    
if __name__ == "__main__":
    ## 载入yaml配置文件
    conf = yaml.safe_load(open("model_train.yaml", 'r') .read())
    files = conf.get("train_files") 
    # 载入instance
    instances = load_instance(files)
    # 处理instance
    train_data = TrainData(instances, conf)