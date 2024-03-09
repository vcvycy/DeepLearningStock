import re, math
import numpy as np 
from test_common import LineItem, Stats, read, read_all_item

def step_read_log(round, end_when = "END"):
    all_items = []
    stats = Stats(prefix = "第%s次运行结果" %(round))
    _all_items = read_all_item()
    print("items size: %s" %(len(_all_items)))
    for item in _all_items:
        if item.label is None or item.raw_label > 900:
            continue
        if args.stock is None or args.stock in item.stock:
            stats.add(item.date, item) 
            stats.add("ALL_TIME", item)
            all_items.append(item)
    print("过滤掉最近没label的: %s" %(len(all_items)))
    return stats, all_items

def step_analysis(round, stats, all_items):
    ######## 统计每个key(ALL_TIME or date) 的正确率
    stats.output_all(args.show_date)
    # return
    ######### 统计相邻两个天数，但是topk相差很大的样本 ###############
    all_items.sort(key = lambda x: "%s:%s" %(x.stock, x.date))
    i = 0
    print("all_items: %s" %(len(all_items)))
    prev_items = []
    next_items = []
    while i < len(all_items):
        stock = all_items[i].stock
        items = [] 
        while i < len(all_items) and stock == all_items[i].stock:
            items.append(all_items[i])
            i += 1
        
        # print(items[0].stock)
        for j in range(len(items)):
            for step in range(2, 3):
                if j + step  >= len(items):
                    continue
                item1 = items[j]
                item2 = items[j + step]
                # if item1.topk > item2.topk:
                #     item1 , item2 = item2, item1
                if item1.topk < 10000 and item2.topk > 100000:
                # if item1.topk < 10000 and item2.topk < 10000:
                    # print("%s VS %s" %(item1, item2))
                    prev_items.append(item1)
                    next_items.append(item2)
    print("同一个股票，相邻两天, 预估排名相差很大".center(100, "-"))
    print("数量： %s" %(len(prev_items)))
    print("rank靠前的平均label: %s raw %s topk: %s " %(
        np.mean([i.label for i in prev_items]), 
        np.mean([i.raw_label for i in prev_items]), 
        np.mean([i.topk for i in prev_items])))
    print("rank靠后的平均label: %s raw %s topk: %s " %(
        np.mean([i.label for i in next_items]), 
        np.mean([i.raw_label for i in next_items]), 
        np.mean([i.topk for i in next_items])))
    return  

def main():
    """
      stock = None, 全部股票一起算，且分天看
      stock != None : 看当前股票
    """
    round = 0
    while True:
        round += 1
        print('-' * 200)
        try:
            stats, all_items = step_read_log(round, end_when = "END")
        except:
            break
        # if len(all_items) < 10000:
        #     continue
        # input("all_item: %s" %(len(all_items)))
        step_analysis(round, stats, all_items) 

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--stock', type=str, default=None) 
    parser.add_argument('-d', '--show-date', action='store_true')
    parser.add_argument('-c', '--certainly-threshold', type=float, default = 0)
    args = parser.parse_args()
    main()