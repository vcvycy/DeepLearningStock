import re, math
import numpy as np 
from common.utils import str2timestamp
from common.tushare_api import TushareApi

def read():
    try:
        return input("")
    except EOFError:
        print("log文件结束!")
        raise EOFError
    except Exception as e:
        print("Exception: %s" %(e))
        exit(0)

def read_all_item(end_when = "END"):
    all_items = [] 
    while True: 
        line = read()
        if end_when in line:
            print("END")
            break 
        try:
            item = LineItem(line) 
        except:
            continue  
        all_items.append(item)
    return all_items

def show_items(all_items, stock_names = [], weekly = False, input_stock = False):
    """
      input_stock : 输入来展示股票
    """
    def draw_stock(stock, all_items, weekly):
        date2score = {}
        for item in all_items:
            if stock == item.stock:
                date2score[str2timestamp(str(item.date), '%Y%m%d') ] = (len(all_items) - item.topk) / len(all_items) -0.5
                # print(item.date)
        ####
        cur_stock = None 
        for item in TushareApi.get_all_stocks():
            if stock in item["name"]:
                cur_stock = item
                break
        if cur_stock is None:
            print("找不到股票: %s" %(stock))
            return 
        print("%s %s" %(cur_stock["name"], cur_stock["ts_code"]))
        get_kline = TushareApi.get_kline_by_ts_code_weekly if weekly else TushareApi.get_kline_by_ts_code
        kline = get_kline(cur_stock["ts_code"], start_date= "20100601", end_date="")
        kline.draw(date2score = date2score, title = "%s round: %s" %(cur_stock["ts_code"], "merge"))
        return 
    # 给items展示要买的股票
    if len(stock_names) == 0:
        lastest_date = np.max([item.date for item in all_items])
        for item in all_items:
            if item.date == lastest_date:
                stock_names.append(item.stock)
        stock_names = stock_names[:1]
        print("没有指定股票，自动取%s top 5的股票： %s" %(lastest_date, stock_names))
    
    for stock in stock_names:
        draw_stock(stock, all_items, weekly)
    while input_stock:
        stock  = input("")
        draw_stock(stock, all_items, weekly)
    return 
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
            self.raw_label = self.get_digit("raw_label: ? ")
            self.label = self.get_digit(" label: ? ")
        except:
            self.label = None
            self.raw_label = None
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
        return "%s %s raw_label: %s label: %s rank %s\n" %(self.stock, self.date, self.raw_label, self.label,self.topk)
    def __repr__(self):
        return str(self)
# line = """INFO 2023-02-03 03:19:16,701 [Top_315957] 恒久科技 20221108 概率: -0.0416 fid_label_avg: 0.0005 label: -0.01899999938905239 raw_label: -0.019 确定性: 0.684 正确率: 0.56"""
# item = LineItem(line)
# print(item)
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

        thresholds = set([2**i for i in range(20)])
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

    def output_all(self, show_date = False):
        """
          输出所有分析数据
        """
        keys = list(self.key2stat)
        keys.sort(key = lambda x : str(x))

        for key in keys: 
            stat = self.key2stat[key]
            stat.gen_one_output()
            if key == "ALL_TIME" or show_date:
                print(("%s-%s" %(self.prefix, key)).center(100, "=")) 
                print(stat.output)
        for buy_topk in [1, 2,4, 8]:
            win_money = []
            win_keys = []
            loss_money = []
            loss_keys = []
            for key in keys: 
                stat = self.key2stat[key]
                if key != "ALL_TIME":
                    assert stat.tot_ins  < 10000, "key = %s total ins = %s" %(key, stat.tot_ins)  # 每天的样本数应该 < 10000
                    win = stat.topk_avg_label.get(buy_topk, 0) - stat.topk_avg_label[stat.tot_ins] # 每天买topk股票 vs 每日大盘指标的收益
                    if win > 0:
                        win_money.append(win)
                        win_keys.append(key)
                    else:
                        loss_money.append(win)
                        loss_keys.append(key)
            print("买top %s 【日平均收益: %.2f%%】,  能跑赢大盘%s天, 平均盈利: %.2f%%, 跑输大盘%s天, 平均跑输: %.2f%%" %(
                buy_topk, np.mean(win_money + loss_money) * 100,
                len(win_money), np.mean(win_money) *100,
                len(loss_money), np.mean(loss_money) *100
                ))
            print("    跑赢大盘日期: %s" %(win_keys))
            print("    跑输大盘日期: %s" %(loss_keys))
        return 
