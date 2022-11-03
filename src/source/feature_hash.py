# raw_feature 处理
import hashlib
def hash_string(s):
    # 字符串hash成54位int
    s = str(s).encode("utf8")
    return int.from_bytes(hashlib.sha256(s).digest()[:8], 'little') & ((1 << 54) -1)

class BaseMethod():
    def __init__(self):
        pass
    def extract(self, single_feature, conf):
        """
          返回feature处理过的特征: 
             如:  数字离散化, single_feature = 1.4, 离散化后，返回1
        """
        return single_feature

    def __call__(self, raw_features, conf, slot): 
        fids = []
        # 原始特征得到int64, 再和slot拼接
        if not isinstance(raw_features, list):
            raw_features = [raw_features]
        
        for single_feature in raw_features:
            """
              example: 
                 single_feature = 1.5
                 extracted_faeture = int(single_feature) = 1
                 hash_i54 = hash_string(1)
            """
            extracted_feature =self.extract(single_feature, conf) 
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
    def extract(self, single_feature, conf):
        assert isinstance(single_feature, float) or isinstance(single_feature, int)
        start = conf.get("start", 0)
        step =conf.get("step", 1) 
        feature = int((single_feature - start) / step)
        return str(feature)

if __name__ == "__main__":
    # for i in range(100):
    # print(hash_string(-0.03001876172607887))
    m = LinearDiscrete()
    print(m([-0.03001876172607887], {'start': 0, 'step': 0.005} , 1))