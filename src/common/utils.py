#coding=utf8
import time
import struct
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
    byte_num = struct.unpack('Q', f.read(8))[0]
    print("byte_num : %s" %(byte_num))
    data = f.read(byte_num)
    if PBClass is not None:
        obj = PBClass()
        obj.ParseFromString(data)
        data = obj
    return byte_num, data
    


def str2timestamp(timestr, format = "%Y-%m-%d %H:%M:%S"): 
    timeArray = time.strptime(timestr, format) 
    return int(time.mktime(timeArray))

def timestamp2str(ts, format = "%Y-%m-%d %H:%M:%S"):
    return time.strftime(format,time.localtime(int(ts)))


if __name__ == "__main__":
    # from stock_pb2 import *
    # path = "/Users/bytedance/OneDrive/DeepLearningStock/src/train_data_pb.bin"
    # f = open(path, "rb")
    # print(read_file_with_size(f, Instance))

    suffix = timestamp2str(time.time(), "%Y%m%d_%H")
    print(suffix)