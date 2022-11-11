from common.utils import *
from common.stock_pb2 import *
if __name__ == "__main__":
    path = "../training_data/data.bin.20221109"
    f = open(path, "rb")
    for i in range(10**10):
        size, data = read_file_with_size(f, Instance)
        if size == 0:
            break
        print('-'* 50 + str(i+1) + '-'*50)
        # print(data)

    # suffix = timestamp2str(time.time(), "%Y%m%d_%H")
    # print(suffix)