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
    data = f.read(data_size)
    if PBClass is not None:
        obj = PBClass()
        obj.ParseFromString(data)
        data = obj
    return data_size, data

def enum_instance(path):
    from common.stock_pb2 import Instance
    f = open(path, "rb")
    while True:
        size, data = read_file_with_size(f, Instance)
        if size == 0:
            break
        yield data
    return 


def str2timestamp(timestr, format = "%Y-%m-%d %H:%M:%S"): 
    timeArray = time.strptime(timestr, format) 
    return int(time.mktime(timeArray))

def timestamp2str(ts, format = "%Y-%m-%d %H:%M:%S"):
    return time.strftime(format,time.localtime(int(ts)))


if __name__ == "__main__":
    def save_ts_code_ins_to(ts_code):
        f = open("debug_%s.data" %(ts_code), "wb")
        for ins in enum_instance("../../training_data/data.bin.20221123_2106"):
            if ts_code in ins.ts_code:
                write_file_with_size(f, ins.SerializeToString())
        f.close()
        return 
    # save_ts_code_ins_to("300438")
    # exit(0)
    ins23s = {ins.date : ins for ins in enum_instance("debug_300438.data")}
    ins25s = {ins.date : ins for ins in enum_instance("../../training_data/data.bin.20221128_1645")}
    print("23日ins数: %s 25日ins数: %s" %(len(ins23s), len(ins25s)))

    dates  = list(set(list(ins23s) + list(ins25s)))
    dates.sort(key = lambda x : x)
    for date in dates:
        if date not in ins25s: 
            print("日期: %s 不在25里" %(date))
            continue
        if date not in ins23s: 
            print("日期: %s 不在23里" %(date))
            continue 
        print("对比 %s数据: " %(date))
        ins23 = ins23s[date]
        ins25 = ins25s[date]
        # for label_name in ins25.label:
        #     if label_name not in ins23.label:
        #         print("label不在label23里: %s" %(label_name))
        #         continue
        #     label23 = ins23.label[label_name]
        #     label25 = ins25.label[label_name]
        #     # print("%s : %s == %s" %(label_name, label23, label25))
        #     assert label23 == label25, "label不一致： %"
        fid23 = set([])
        for fc in ins23.feature:
            for fid in fc.fids:
                if fid>>54 >= 200 or fid>>54 <= 4:
                    continue
                fid23.add(fid)
    
        fid25 = set([])
        for fc in ins25.feature:
            for fid in fc.fids:
                if fid>>54 >= 200 or fid>>54 <= 4:
                    continue
                fid25.add(fid)
        # print("fid数量对比： %s vs %s" %(len(fid23), len(fid25)))
        show = False
        for fid in fid25:
            if fid not in fid23:
                show = True
                print("fid25的fid: %s(slot: %3d) 不在fid23中" %(fid, fid>>54))
        for fid in fid23:
            if fid not in fid25:
                print("fid23的fid: %s(slot: %3d) 不在fid25中" %(fid, fid>>54))