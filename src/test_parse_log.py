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
class OneStat:
    def __init__(self):
        self.tot_ins = 0          # 总数
        self.pos_ins = 0          # 正例数
        self.raw_label_sum = 0    # sum(原始label)
        self.topk_sum = 0         # sum(模型rank)
        self.topk_avg_label = {}
        self.output = ""
        return 

    def add(self,line_item):
        self.tot_ins += 1
        self.pos_ins += 1 if line_item.label > 0 else 0
        self.raw_label_sum += line_item.raw_label
        self.topk_sum += line_item.topk

        thresholds = set([5 * 2**i for i in range(20)])
        if self.tot_ins in thresholds: 
            self.gen_one_output()
        return 
    def gen_one_output(self):
        ## 数量达到某个阈值，则生成一条输出
        self.output += "总数: %5d, 真实数量: %5d 正确率: %.2f%% 原始label均值: %.1f%% 平均排名: %.1f\n"  %(
            self.tot_ins, 
            self.pos_ins, 
            100* self.pos_ins/self.tot_ins, 
            100* self.raw_label_sum / self.tot_ins,  
            self.topk_sum/self.tot_ins)
        self.topk_avg_label[self.tot_ins] = self.raw_label_sum / self.tot_ins
        return 

class Stats:
    def __init__(self, prefix = ""):
        self.prefix = prefix 
        self.key2stat = {}
        return 
    def add(self, key, line_item):
        if key not in self.key2stat:
            self.key2stat[key] = OneStat()
        self.key2stat[key].add(line_item)
        return 

    def output_all(self):
        """
          输出所有分析数据
        """
        keys = list(self.key2stat)
        keys.sort(key = lambda x : str(x))

        win_money = []
        win_keys = []
        loss_money = []
        loss_keys = []
        for key in keys: 
            stat = self.key2stat[key]
            stat.gen_one_output()
            if key == "ALL_TIME" or args.show_date:
                print(("%s-%s" %(self.prefix, key)).center(100, "=")) 
                print(stat.output)
            if key != "ALL_TIME":
                assert stat.tot_ins  < 10000  # 每天的样本数应该 < 10000
                win = stat.topk_avg_label[5] - stat.topk_avg_label[stat.tot_ins] # 相比pct xx股票利润
                if win > 0:
                    win_money.append(win)
                    win_keys.append(key)
                else:
                    loss_money.append(win)
                    loss_keys.append(key)
        
        print("买top 5能跑赢大盘%s天, 平均盈利: %.2f%%, 跑输大盘%s天, 平均跑输: %.2f%%" %(
            len(win_money), np.mean(win_money) *100,
            len(loss_money), np.mean(loss_money) *100
            ))
        print("跑赢大盘日期: %s" %(win_keys))
        print("跑输大盘日期: %s" %(loss_keys))
        return 

def read():
    try:
        return input("")
    except Exception as e:
        print("Exception: %s" %(e))
        exit(0)

def step_read_log(round):
    all_items = []
    stats = Stats(prefix = "第%s次运行结果" %(round))
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
        stats.add(item.date, item) 
        stats.add("ALL_TIME", item)
        all_items.append(item)
    return stats, all_items

def step_analysis(round, stats, all_items):
    ######## 统计每个key(ALL_TIME or date) 的正确率
    stats.output_all()
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
        stats, all_items = step_read_log(round)
        step_analysis(round, stats, all_items) 

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--stock', type=str, default=None) 
    parser.add_argument('-d', '--show-date', action='store_true')
    parser.add_argument('-c', '--certainly-threshold', type=float, default = 0)
    args = parser.parse_args()
    main()