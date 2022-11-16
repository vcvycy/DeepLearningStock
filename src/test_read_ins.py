from common.utils import *
from common.stock_pb2 import *
import sys
import argparse
parser = argparse.ArgumentParser()

if __name__ == "__main__":
    parser.add_argument('-p', '--path', type=str, required=True)
    parser.add_argument('-t', '--ts-code', type=str, default=None)
    parser.add_argument('-d', '--date', type=str, default=None)
    parser.add_argument('-f', '--fids', type=str, default="")    #包含此fid
    # parser.add_argument('-s', '--slots', type=str, default="")    #包含此fid
    args = parser.parse_args()

    f = open(args.path, "rb")
    # print("f=%s" %(f))
    if  args.fids != "":
        contain_fids = set([int(f) for f in args.fids.split(",")])
    else:
        contain_fids = set([])
    for i in range(10**10):
        size, data = read_file_with_size(f, Instance)
        if size == 0:
            break
        if args.ts_code is not None and  args.ts_code not in data.ts_code:
            continue
        if args.date is not None and data.date != args.date:
            continue
        if args.fids != "":
            contain = 0
            for fc in data.feature:
                for fid in fc.fids:
                    if fid in contain_fids:
                        contain += 1
            if contain < len(contain_fids):
                continue
        print('-'* 50 + str(i+1) + '-'*50)
        print(data)
        input("press any key to continue...")

    # suffix = timestamp2str(time.time(), "%Y%m%d_%H")
    # print(suffix)