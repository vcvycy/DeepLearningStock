# raw_feature 处理
import hashlib
def hash_string(s):
    # 字符串hash成54位int
    s = str(s).encode("utf8")
    return int.from_bytes(hashlib.sha256(s).digest()[:8], 'little') & ((1 << 54) -1)

class BaseMethod():
    def __init__(self):
        pass
    def execute(self, raw_features, conf):
        raise Exception("BaseMethod need override")
    def __call__(self, raw_features, conf, slot): 
        fids = []
        # 原始特征得到int64, 再和slot拼接
        for f in self.execute(raw_features, conf):
            fids.append((slot << 54) + f) 
        return fids

class LinearDiscrete(BaseMethod):
    """
       线性分桶离散化: 
         start = 0
         step = 2
         则 0~2那的数都抽到同一个fid
    """
    def execute(self, raw_features, conf):
        start = conf.get("start", 0)
        step =conf.get("step", 1)
        raw_feature = raw_features[0]
        raw_feature = int((raw_feature - start) / step)
        return [hash_string(raw_feature)]

if __name__ == "__main__":
    # for i in range(100):
    print(hash_string(-0.03001876172607887))
    m = LinearDiscrete()
    m([-0.0300], {'start': 0, 'step': 0.005} , 1)