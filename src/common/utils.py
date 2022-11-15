#coding=utf8
import time
import struct

def timestamp2str(ts, format = "%Y-%m-%d %H:%M:%S"):
    return time.strftime(format,time.localtime(ts))
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
    data = f.read(data_size)
    if PBClass is not None:
        obj = PBClass()
        obj.ParseFromString(data)
        data = obj
    return data_size, data
    


def str2timestamp(timestr, format = "%Y-%m-%d %H:%M:%S"): 
    timeArray = time.strptime(timestr, format) 
    return int(time.mktime(timeArray))

def timestamp2str(ts, format = "%Y-%m-%d %H:%M:%S"):
    return time.strftime(format,time.localtime(int(ts)))


if __name__ == "__main__":
    from stock_pb2 import *
    path = "../../training_data/data.bin.20221103"
    f = open(path, "rb")
    for i in range(1000):
        size, data = read_file_with_size(f, Instance)
        if size == 0:
            break
        print('-'* 50 + str(i) + '-'*50)
        print(data)

    # suffix = timestamp2str(time.time(), "%Y%m%d_%H")
    # print(suffix)