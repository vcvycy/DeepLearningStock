from common.utils import *
from common.stock_pb2 import *
import sys
import argparse
parser = argparse.ArgumentParser()

if __name__ == "__main__":
    parser.add_argument('-p', '--path', type=str, required=True)
    parser.add_argument('-t', '--ts-code', type=str, default=None)
    parser.add_argument('-d', '--date', type=str, default=None)
    args = parser.parse_args()

    f = open(args.path, "rb")
    for i in range(10**10):
        size, data = read_file_with_size(f, Instance)
        if size == 0:
            break
        if args.ts_code is not None and data.ts_code != args.ts_code:
            continue
        if args.date is not None and data.date != args.date:
            continue

        print('-'* 50 + str(i+1) + '-'*50)
        print(data)
        input("press any key to continue...")

    # suffix = timestamp2str(time.time(), "%Y%m%d_%H")
    # print(suffix)