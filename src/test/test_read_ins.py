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
        size, ins = read_file_with_size(f, Instance)
        if size == 0:
            break
        if args.ts_code is not None and  args.ts_code not in ins.ts_code and args.ts_code not in ins.name:
            continue
        # if ins.date >= '20230101':
        #     continue
        if args.date is not None and ins.date != args.date:
            continue

        # if "ETF" in ins.name or "LOF" in ins.name:
        #     continue
        skip = False
        contain = 0
        for fc in ins.feature:
            # if fc.slot == 101 and int(fc.extracted_features[0]) < 6:
            #     skip = True
            #     break
            # if fc.slot == 50 and int(fc.extracted_features[0]) < 2:
            #     skip = True
            #     break
            # if fc.slot == 131 and int(fc.extracted_features[0]) > -2:
            #     skip = True
            #     break
            # if fc.slot in [101, 50, 151]:
            #     print("%s %s" %(int(fc.extracted_features[0]), fc.slot))
            #     input('..')
            for fid in fc.fids:
                if fid in contain_fids:
                    contain += 1
        if contain < len(contain_fids) or skip:
            continue
        slots = set([])
        for fc in ins.feature:
            for fid in fc.fids:
                slots.add(fid>>54)
        print("slots: %s(%s)" %(len(slots), slots))
        print('-'* 50 + str(i+1) + '-'*50)
        print(ins)
        print("名字: %s 市值: %s" %(ins.name, ins.total_mv))
        input("press any key to continue...")

    # suffix = timestamp2str(time.time(), "%Y%m%d_%H")
    # print(suffix)