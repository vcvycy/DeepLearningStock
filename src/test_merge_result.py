from common.utils import str2timestamp

from test_common import LineItem, Stats, read_all_item, show_items
from common.tushare_api import TushareApi
import numpy as np
import argparse

def merge_items(items):
    topk = np.mean([item.topk for item in items])
    item = items[0]
    item.topk = topk
    item.pos_rate = 0
    item.prob = 0
    return item
def main():
    """
      stock = None, 全部股票一起算，且分天看
      stock != None : 看当前股票
    """
    round = 0
    key2items = {}
    all_num = 0
    # 合并排序位置topk
    while True:
        try:
            round += 1
            print('-' * 200)
            all_items = read_all_item(end_when = "END")
            if len(all_items) < 10000:
                continue 
            all_num += len(all_items)
            print("size: %s" %(len(all_items)))
            for item in all_items:
                # if item.label is None:
                #     continue
                key = "%s-%s" %(item.stock, item.date)
                if key not in key2items:
                    key2items[key] = []
                key2items[key].append(item)
        except:
            break
        # break
    print("key2items size: %s %s" %(len(key2items), all_num))
    items = [merge_items(key2items[key]) for key in key2items]
    items.sort(key = lambda x : x.topk)
    stats = Stats(prefix = "合并结果")
    for item in items:
        if item.label is None:
            continue
        stats.add(item.date, item) 
        stats.add("ALL_TIME", item)
    stats.output_all()
    # for key in key2items:
    #     items = key2items[key]
    #     print("%s %s" %(key, items))
    if args.stocks == "":
        show_items(items)
    else:
        show_items(items, stock_names = args.stocks.split(","))
    return 

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--stocks', type=str, default="") 
    args = parser.parse_args()
    main()