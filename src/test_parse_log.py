import re, math
import numpy as np
tot = {}
corr = {}
raw_label_sum = {}
rank = {}
outputs = {}
thresholds = set([20 * 2**i for i in range(20)])
class LineItem:
    """
      解析数据：
      INFO 2023-01-08 22:56:16,313 [Top_208383] 上海梅林 20221020 概率: 0.3650 fid_label_avg: 0.4159 label: 1 raw_label: 0.036 确定性: 0.668 正确率: 0.41
    """
    def __init__(self, line): 
        # if "END" in line:  # 表示分隔符
        assert "Top_" in line
        self.line = line
        # self.type = self.get_type()
        self.topk = self.get_digit("Top_?", int)
        self.date = self.get_digit(" ? 概率", int)
        self.prob = self.get_digit("概率: ? ")
        try:
            self.label = self.get_digit("label: ? ", int)
        except:
            self.label = None
        assert self.label is not None
        self.raw_label = self.get_digit("raw_label: ? ")
        self.certainly = self.get_digit("确定性: ? ")
        self.pos_rate = self.get_digit("正确率: ?")
        self.stock = re.findall("Top_\d+\] ([^ ]+)", self.line)[0]
        return 
    def get_digit(self, pat, fun = float):
        if "?" in pat:
            digit_reg_pattern = "(-?[0-9.]+)"
            pattern = pat.replace("?", digit_reg_pattern)
        else:
            pattern = pat
        value = fun(re.findall(pattern, self.line)[0])
        # print("%s = %s" %(pat, value))
        return value
    def __str__(self):
        return "%s %s %s rank %s\n" %(self.stock, self.date, self.raw_label, self.topk)
    def __repr__(self):
        return str(self)
# line = 'INFO 2023-01-08 22:56:16,309 [Top_208371] 麦迪科技 20230103 概率: 0.3650 fid_label_avg: 0.4279 label: None raw_label: 999.000 确定性: 0.200 正确率: 0.41'
# item = LineItem(line)
# print(item.stock)
# exit(0)
# class Stats:
#     def __init__(self): 
#         self.tot = {}           # 所有数量
#         self.corr = {}          # 正例数量
#         self.raw_label_sum = {} # 原始label
#         # self.
#         return 

def add_stats(date, label, raw_label, topk):
    global tot 
    global corr 
    global raw_label_sum
    global thresholds
    global rank
    if date not in tot:
        tot[date] = 0
        corr[date] = 0
        rank[date] = 0
        outputs[date] = ""
        raw_label_sum[date] = 0
    tot[date] += 1
    corr[date] += label
    rank[date] +=  topk
    raw_label_sum[date] += raw_label
    if tot[date] in thresholds: 
        outputs[date] += "总数: %5d, 真实数量: %5d 正确率: %.2f%% 原始label均值: %.1f%% 平均排名: %.1f\n"  %(tot[date], 
            corr[date], 100*corr[date]/tot[date], 100* raw_label_sum[date] / tot[date],  rank[date]/tot[date])
    return 

def read():
    try:
        return input("")
    except Exception as e:
        print("Exception: %s" %(e))
        exit(0)

def process_round(args, round):
    print('-' * 200)
    global tot 
    global corr 
    global raw_label_sum
    global rank
    global outputs
    tot = {}
    corr = {}
    raw_label_sum = {}
    rank = {}
    outputs = {}
    certain_filter_cnt = 0
    all_items = []
    while True: 
        line = read()
        if "END" in line:
            print("END")
            break
        if "conf" in line:
            print(line)
        try:
            item = LineItem(line)
            # 过滤
            assert args.stock is None or args.stock in item.stock
            # assert item.topk < 1000
        except:
            continue 
        label = item.label 
        raw_label = item.raw_label
        if args.show_date:
            add_stats(item.date, label, raw_label, item.topk) 
        add_stats("ALL_TIME", label, raw_label, item.topk)
        all_items.append(item)
    dates = list(tot)
    dates.sort(key = lambda x : str(x))
    for date in dates: 
        print(("第%s次运行结果-%s" %(round,date)).center(100, "=")) 
        print(outputs[date])
        print( "总数: %5d, 正例数量: %5d 正确率: %.2f%% 原始label均值: %.1f%% 平均排名: %.1f\n"  %(tot[date], 
                corr[date], 100*corr[date]/tot[date], 100*raw_label_sum[date] / tot[date],  rank[date]/tot[date]))
    print("注: 过滤确定性低的股票： %s个" %(certain_filter_cnt))

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
        
    # print(all_items[:100])
    

def main(args):
    """
      stock = None, 全部股票一起算，且分天看
      stock != None : 看当前股票
    """
    round = 0
    while True:
        round += 1
        process_round(args, round)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--stock', type=str, default=None) 
    parser.add_argument('-d', '--show-date', action='store_true')
    parser.add_argument('-c', '--certainly-threshold', type=float, default = 0)
    args = parser.parse_args()
    main(args)