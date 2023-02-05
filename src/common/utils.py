#coding=utf8
import time
import struct

# 浮点数保留k位小数
def float_trun(f, k = 3):
    try:
        f = float(f)
        return 1.0 * int(f * 10 ** k) / (10 ** k) 
    except:
        return f

def pretty_json(data, prefix = ""):
    def show(data, prefix= ""):
        s = ""
        for k in data:
            v = data[k]
            if isinstance(v, dict):
                s += "%s %s:\n%s" %(prefix, k, show(v, prefix+"  "))
            else: 
                val = str(v).replace("\n", " ")
                if len(val) > 300:
                    val = val[:300] + "...(共%s字符)" %(len(val))
                s += "%s %s: %s\n" %(prefix, k, val)
        return s
    data = show(data, prefix)
    return data

def write_file_with_size(f, binary):
    """
      二进制数据保存到文件中, 字节数8位存在前8
    """
    size = len(binary) 
    f.write(struct.pack('Q', size))
    f.write(binary)
    return 

def read_file_with_size(f, PBClass = None):
    data_size_bin = f.read(8)
    if len(data_size_bin) < 8:
        return 0, None
    data_size = struct.unpack('Q', data_size_bin)[0]
    assert data_size < 2**20
    data = f.read(data_size)
    if PBClass is not None:
        obj = PBClass()
        obj.ParseFromString(data)
        data = obj
    return data_size, data

def enum_instance(path, max_ins = 1e10):
    """
      path : 训练文件，可以单个，或者多个
      max_ins: 最多读取多少样本
    """
    from common.stock_pb2 import Instance
    if not isinstance(path, list):
        path = [path]
    for p in path:
        f = open(p, "rb")
        while True:
            size, data = read_file_with_size(f, Instance)
            if size == 0 or max_ins <= 0:
                break
            max_ins -= 1
            yield data
    return 


def str2timestamp(timestr, format = "%Y-%m-%d %H:%M:%S"): 
    timeArray = time.strptime(timestr, format) 
    return int(time.mktime(timeArray))

def timestamp2str(ts, format = "%Y-%m-%d %H:%M:%S"):
    return time.strftime(format,time.localtime(int(ts)))


# if __name__ == "__main__": 