from common.utils import *
from common.stock_pb2 import * 
import os
import numpy as np
if __name__ == "__main__":
    paths = [
        "../training_data/data.daily.20240213_1725",
        "../training_data/data.daily.20240123_1802"
    ]
    k = 'next_7d_14d_mean_price'
    fid2label = {}
    for ins in enum_instance(paths, max_ins=1e15):
        if k not in ins.label:
            # input(ins.label)
            continue

        label = ins.label[k]
        for f in ins.feature:
            fid = "%s:%s:%s" %(f.slot, f.fids[0], f.name)
            if fid not in fid2label:
                fid2label[fid] = []
            fid2label[fid].append(label)
    
    data = [(fid, np.mean(fid2label[fid]), len(fid2label[fid])) for fid in fid2label]
    data.sort(key = lambda x : x[1])
    for fid, label, n in data:
        print("%.3f %6s %s" %(label, n, fid))