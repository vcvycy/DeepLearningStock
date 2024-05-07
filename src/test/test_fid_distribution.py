from common.utils import *
from common.stock_pb2 import *
import sys
import argparse
import matplotlib.pyplot as plt
import numpy as np
parser = argparse.ArgumentParser()
def get_fid_occur():
    fid2date_count = {}  # 统计
    dates = set([])
    paths = [
        # "../training_data/data.daily.20230608_1855",
        # "../training_data/data.daily.20230607_1837",
        "../training_data/data.daily.20230606_1755"
    ] 
    for ins in enum_instance(paths): 
        if ins.date == "":
            break
        date = int(ins.date)     # date格式为20220101
        dates.add(date)
        for fc in ins.feature:
            for fid in fc.fids:
                if fid not in fid2date_count:
                    fid2date_count[fid] = {}
                if date not in fid2date_count[fid]:
                    fid2date_count[fid][date] = 0
                fid2date_count[fid][date] +=1 
    dates = list(dates)
    dates.sort()
    date2index = {date: idx for idx, date in enumerate(dates)}
    print(date2index)
    fid_var_pair = []
    for fid in fid2date_count:
        date_count = fid2date_count[fid] 
        y = [date_count.get(d, 0) for d in dates]
        fid_var_pair.append((fid, np.var(y)))
    
    fid_var_pair.sort(key = lambda x : x[1])
    for fid, var in fid_var_pair:
        print("fid : %s var: %.3f" %(fid, var))
    while True:
        try:
            fid = int(input("输入fid"))
            date_count = fid2date_count[fid]
            x = []
            y = []
            for i, d in enumerate(dates):
                x.append(i)
                y.append(date_count.get(d, 0))
            print(date_count)
            plt.plot(x, y, label="fid: %s" %(fid))
            plt.show()
        except Exception as e:
            print("Excep: %s" %(e))
    return 

if __name__ == "__main__":
    parser.add_argument('-t', '--ts-code', type=str, default=None)
    parser.add_argument('-d', '--date', type=str, default=None)
    parser.add_argument('-f', '--fids', type=str, default="")    #包含此fid
    # parser.add_argument('-s', '--slots', type=str, default="")    #包含此fid
    args = parser.parse_args()
    get_fid_occur() 