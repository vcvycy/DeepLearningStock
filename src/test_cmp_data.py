from common.utils import *
from common.stock_pb2 import * 
import os

def step_1_save_ins(f1, f2, ts_code):
    print("step1".center(100,"-"))
    # 把两个Instance文件抽出对应的ts_code数据，然后保存到临时文件中
    def save_ts_code_ins_to(src_file,ts_code):
        dst_file = "%s.%s" %(src_file, ts_code)    
        if os.path.exists(dst_file):
            print("step1 已经执行过，文件%s存在" %(dst_file))
            return dst_file
        f = open(dst_file, "wb")
        num  =0
        print("保存%s的instance : %s -> %s" %(ts_code, src_file, dst_file))
        for ins in enum_instance(src_file):
            if ts_code in ins.ts_code:
                num +=1
                write_file_with_size(f, ins.SerializeToString())
        print("保存instance数量: %s" %(num))
        f.close()
        return dst_file
    
    return save_ts_code_ins_to(f1, ts_code), save_ts_code_ins_to(f2, ts_code)

def step_2_cmp_ins(f1, f2, ts_code):
    print("step2".center(100,"-"))
    ins1s =  {ins.date : ins for ins in enum_instance(f1)}
    ins2s =  {ins.date : ins for ins in enum_instance(f2)}
    print("ins数  %s vs %s" %(len(ins1s), len(ins2s)))
    
    dates  = list(set(list(ins1s) + list(ins2s)))
    for date in dates:
        if date not in ins2s: 
            print("日期: %s 不在f2里" %(date))
            continue
        if date not in ins1s: 
            print("日期: %s 不在f1里" %(date))
            continue 
        ins1 = ins1s[date]
        ins2 = ins2s[date]
        prefix = "[%s-%s]" %(ins1.ts_code, date)
        for label_name in ins2.label:
            if label_name not in ins1.label:
                print("%s label2不在label1里: %s" %(prefix, label_name))
                continue
            label23 = ins1.label[label_name]
            label25 = ins2.label[label_name]
            # print("%s : %s == %s" %(label_name, label23, label25))
            assert label23 == label25, "label不一致： %"
        slot2fc1 = {}
        for fc in ins1.feature:
            for fid in fc.fids: 
                slot2fc1[fid>>54] = fc
    
        slot2fc2 = {}
        for fc in ins2.feature:
            for fid in fc.fids:
                slot2fc2[fid>>54] = fc
        assert len(slot2fc1) == len(slot2fc2), "slot不一样"
        for s in slot2fc1:
            fid1 = slot2fc1[s].fids[0]
            fid2 = slot2fc2[s].fids[0]
            if fid1 != fid2:
                print("{} slot {} 不一样".format(prefix,s).center(80, "-"))
                print("feature column1: %s" %(slot2fc1[s]))
                print("feature column2: %s" %(slot2fc2[s]))

    return 

if __name__ == "__main__":
    f1 = "../training_data/data.bin.20221128_1646"
    f2 = "../training_data/data.bin.20221129_1633"
    ts_code = "600619"

    ts_f1, ts_f2 = step_1_save_ins(f1, f2, ts_code) 
    step_2_cmp_ins(ts_f1, ts_f2, ts_code)