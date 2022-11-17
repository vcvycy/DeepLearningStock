# raw_feature 处理
import hashlib
import math
import sys
sys.path.append("..")
from common.utils import *
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
        return features[0]

    def __call__(self, raw_features, conf, slot): 
        assert slot > 0 and isinstance(raw_features, list)
        fids = []
        # 原始特征做hash，然后拼接slot
        extracted_feature = str(self.extract(raw_features, conf))
        # print(extracted_feature)
        hash_i54 = hash_string(extracted_feature)
        fids.append((slot << 54) + hash_i54) 
        return [extracted_feature], fids
        
class LinearDiscrete(BaseMethod):
    """
       线性分桶离散化: 
         start = 0
         step = 2
         则 0~2那的数都抽到同一个fid
    """
    def extract(self, features, conf):
        INF = 10**10
        f = features[0]
        assert isinstance(f, float) or isinstance(f, int), "feature: %s" %(f)
        start = conf.get("start", 0)
        step =conf.get("step", 1)
        # 区间内
        f = min(f, conf.get("max", INF))
        f = max(f, conf.get("min", -INF))
        feature = math.floor((f - start) / step)
        return str(feature)

class DateDiffDiscrete(BaseMethod):
    """
        计算两个时间的diff离散化 
    """
    def extract(self, features, conf):
        format = conf.get("format", "%Y%m%d")
        d1, d2 = features[0], features[1]
        try:
            diff_in_days = (str2timestamp(d2, format) - str2timestamp(d1, format))/86400
        except:
            diff_in_days = 0
        
        # step =conf.get("step", 30)
        # feature = math.floor(diff_in_days / step)
        base = conf.get("base", 2)   # 底数 
        feature = math.floor(math.log(diff_in_days +1) /math.log(base))
        return str(feature)

class PositionDiscrete(BaseMethod):
    """
       计算当前点位的位置，然后离散化: 
        pos = (d[0] - d[1])/(d[2]-d[1])
        如depends = 30, 10, 90, 
        则 (30-10)/ (90-10) = 0.25
    """
    def extract(self, fs, conf):
        assert fs[0] >= fs[1] and fs[0] <= fs[2], "[PositionDiscrete] %s" %(fs)
        step =conf.get("step", 0.1)
        k = (fs[0] - fs[1]) / (fs[2] - fs[1])
        feature = math.floor(k / step)
        return str(feature)


class LogDiscrete(BaseMethod):
    """
       Log分桶离散化: 
            以conf.base为底数做log
    """
    def extract(self, features, conf):
        f = features[0]
        INF = 10**10
        assert isinstance(f, float) or isinstance(f, int), "f is not float/inf%s" %(features)
        base = conf.get("base", 2)   # 底数 
        feature = math.floor(math.log(f) /math.log(base))
        return str(feature)

class ChangeRateDiscrete(BaseMethod):
    """
       depend[0]/depend[1] -1, 然后离散化  
    """
    def extract(self, features, conf):
        INF = 10**10
        assert len(features) == 2, "[ChangeRateDiscrete] len !=2 %s" %(features)
        f0, f1 = features[0], features[1]
        step =conf.get("step", 0.1)
        feature = math.floor((f0/f1 - 1) /step)      # floor使得-0.5映射到-1, 0.5 映射到1
        feature = min(feature, conf.get("max", INF))
        return str(feature)


if __name__ == "__main__":
    # for i in range(100):
    # print(hash_string(-0.03001876172607887))
    # m = LinearDiscrete()
    # print(m([-0.03001876172607887], {'base': 2} , 1))
    # m = LogDiscrete()
    # print(m([91578.18491666667], {'base': 2}, 6))
    # m = ChangeRateDiscrete()
    # for i in [-3, -2, -1, 0, 1, 2, 3,4]:
    #     print(m([i, 2], {"step" : 1}, 1))
    m = DateDiffDiscrete()
    print(m(["20221101", "20221111"], {"step" : 1}, 136))