# raw_feature 处理
import hashlib
import math
def hash_string(s):
    # 字符串hash成54位int
    s = str(s).encode("utf8")
    return int.from_bytes(hashlib.sha256(s).digest()[:8], 'little') & ((1 << 54) -1)

class BaseMethod():
    def __init__(self):
        pass
    def extract(self, features, conf):
        """
          返回feature处理过的特征: 
             如:  数字离散化, features = 1.4, 离散化后，返回1
        """
        return features

    def __call__(self, raw_features, conf, slot): 
        assert slot > 0 and isinstance(raw_features, list)
        fids = []
        # 原始特征做hash，然后拼接slot
        extracted_feature =self.extract(raw_features, conf) 
        # print(extracted_feature)
        hash_i54 = hash_string(extracted_feature)
        fids.append((slot << 54) + hash_i54) 
        return fids
        
class LinearDiscrete(BaseMethod):
    """
       线性分桶离散化: 
         start = 0
         step = 2
         则 0~2那的数都抽到同一个fid
    """
    def extract(self, features, conf):
        INF = 10**10
        assert isinstance(features, float) or isinstance(features, int), "feature: %s" %(features)
        start = conf.get("start", 0)
        step =conf.get("step", 1)
        # 区间内
        features = min(features, conf.get("max", INF))
        features = max(features, conf.get("min", -INF))
        feature = int((features - start) / step)
        return str(feature)

class LogDiscrete(BaseMethod):
    """
       Log分桶离散化: 
            以conf.base为底数做log
    """
    def extract(self, features, conf):
        INF = 10**10
        assert isinstance(features, float) or isinstance(features, int)
        base = conf.get("base", 2)   # 底数 
        feature = int(math.log(features) /math.log(base))
        return str(feature)

class ChangeRateDiscrete(BaseMethod):
    """
       depend[0]/depend[1] -1, 然后离散化  
    """
    def extract(self, features, conf):
        assert len(features) == 2, "[ChangeRateDiscrete] len !=2 %s" %(features)
        f1, f2 = features[0], features[1]
        step =conf.get("step", 0.1)
        feature =  int((f1/f2 - 1) /step)
        return feature


if __name__ == "__main__":
    # for i in range(100):
    # print(hash_string(-0.03001876172607887))
    # m = LinearDiscrete()
    # print(m([-0.03001876172607887], {'base': 2} , 1))
    # m = LogDiscrete()
    # print(m([91578.18491666667], {'base': 2}, 6))
    m = ChangeRateDiscrete()
    print(m([[2, 3]], {"step" : 0.1}, 1))