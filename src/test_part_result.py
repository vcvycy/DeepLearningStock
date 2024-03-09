import json
import numpy as np  # Import numpy for np.mean
from common.utils import *
import math
def group_by_key(all_items, key):
    key2items = {}
    for item in all_items:
        k = item[key]
        if k not in key2items:
            key2items[k] = []
        key2items[k].append(item)
    return key2items

def analyse_1(all_items): 
    all_items.sort(key = lambda x : -x['pred']) 
    def get_stats(items):
        pos_count = 0
    
        for item in items:
            if item['label'] > 0:
                pos_count += 1 
        n = len(items)
        ret = {
            "总数" : len(items),
            "收益>0数量" : pos_count,
            "胜率" : "%.2f%%" %(100.0*pos_count / len(items)),
            "平均Label" : "%.2f%%" %(100.0*np.mean([item['label'] for item in items])),
            coloring("平均原始Label", color = 'green') : coloring("%.2f%%" %(100.0*np.mean([item['raw_label'] for item in items])), color = 'green'),
            "平均排名" : "%.0f" %np.mean([item['rank'] for item in items]),
            "AvgLabel-靠后一半" : "%.2f%%" %(100.0*np.mean([item['label'] for item in items[int(n/2):n]])),
        }
        return ret
    topk = 1
    metrics = []
    while topk < len(all_items):
        metrics.append(get_stats(all_items[:topk]))
        topk *= 2
    metrics.append(get_stats(all_items))
    mprint(metrics, title = "analyse 1: topk股票的收益")
    return 
def analyse_2(all_items): 
    all_items.sort(key = lambda x: "%s:%s" %(x["name"], x['date']))

    print("analyse_2: 同一个股票, 相邻1~2天预估分差很多".center(100, '-'))
    name2items = group_by_key(all_items, "name")

    prev_items = []
    next_items = []
    for name in name2items:
        items = name2items[name]
        for j in range(len(items)):
            for interval in range(2, 3):
                if j + interval >= len(items):
                    continue
                item1 = items[j]
                item2 = items[j + interval]
                if item1['rank'] < 10000 and item2['rank'] > 100000:
                    prev_items.append(item1)
                    next_items.append(item2) 

    print(f"数量： {len(prev_items)}")
    # Use list comprehension with dictionary syntax for mean calculations
    print("rank靠前的平均label: %.4f raw %.4f rank: %.0f " % (
        np.mean([i['label'] for i in prev_items]),
        np.mean([i['raw_label'] for i in prev_items]),
        np.mean([i['rank'] for i in prev_items])))
    print("rank靠后的平均label: %.4f raw %.4f rank: %.0f " % (
        np.mean([i['label'] for i in next_items]),
        np.mean([i['raw_label'] for i in next_items]),
        np.mean([i['rank'] for i in next_items])))
    summary = []
    for i in range(5):
        p = prev_items[i]
        n = next_items[i]
        summary.append({
            "name" : p['name'],
            "date" : p["date"] + "~" + n["date"],
            "prev_rank" : p['rank'],
            "prev_label" : p["label"],
            "prev_pred" : p["pred"],
            "next_rank" : n["rank"],
            "next_label" : n["label"],
            "next_pred" : n["pred"],
        })
    # print(summary)
    # print("例如: ")
    # mprint(summary)
    return

def analyse_3(all_items):
    summary = []
    def add_summary(date2profit, topk):
        profit_list = [date2profit[d] for d in date2profit]
        summary.append({
                "每天购买TopK" : str(topk),
                "日平均收益" : "%.2f%%" %(100.0 * np.mean(profit_list)),
                "中位数收益" : "%.2f%%" %(100.0 * np.percentile(profit_list, 50)),
                "天数" : len(date2profit)
            })
        return 
    all_items.sort(key = lambda x : x['rank'])
    date2items = group_by_key(all_items, "date") 

    for topk in [2,4, 8, 16, 32, 64, 128, 9999]:#, 8, 9999, -128, -32, -8]:
        date2topk_profit = {}
        for date in date2items:
            if topk > 0:
                items = date2items[date][:topk]   # 取每天的topk股票
            else:
                items = date2items[date][topk:]   # 取每天的topk股票
            date2topk_profit[date] = np.mean([item['label'] for item in items])  # topk股票的平均label 
        add_summary(date2topk_profit, f"top_{topk}")
        topk_profits = [date2topk_profit[k] for k in date2topk_profit]
    print("analyse_3 购买topk和平均买的收益".center(100, "-"))
    mprint(summary)
    return 

def analyse_4(all_items):
    """计算distill softmax的确定性(确定性越高，说明方差越大)
    """
    all_items = [item for item in all_items if item['rank'] < 10000]
    all_items.sort(key = lambda x : -x['distill_var'])
    i = 20
    while True:
        confidence = np.mean([math.fabs(item['distill_var']) for item in all_items[:i]])
        pred_diff = np.mean([math.fabs(item['label'] - item['pred']) for item in all_items[:i]])
        print(f"top {i} 预估确定性是: %.5f 预估和label差值: %.5f" %(confidence, pred_diff))
        if i > len(all_items):
            break
        i *= 2
    mprint(all_items[:30] + all_items[-10:], col_names = ["name", "date", "rank", "label", "pred", "distill_var"])
    return 
def analyse_5(all_items):
    dates = list(set([item['date'] for item in all_items]))
    dates.sort(key = lambda x : -int(x))
    for d in dates[:2]:# + dates[30:40]:
        cur_items = [item for item in all_items if item['date'] == d][:10]
        summary = {
            "name" : "ALL",
            "date" : d,
            "rank" : int(np.mean([x['rank'] for x in cur_items])),
            "label" : np.mean([x['label'] for x in cur_items]) if cur_items[0]['label'] else '-',
            "pred" : np.mean([x['pred'] for x in cur_items]),
            "distill_var" : np.mean([x['distill_var'] for x in cur_items]),
        }
        mprint(cur_items +[summary], col_names = ["name", "date", "rank", "label", "pred", "distill_var"], \
                title = f"{d}的收益最高股票")
    return 
def analyse(round, all_items):
    all_items.sort(key = lambda x : -x['pred'])
    for i, item in enumerate(all_items):
        item['rank'] = i + 1
    # print("原始items size: %s" %(len(all_items))) 
    items_has_label = [item for item in all_items if item['label'] is not None and not math.isnan(item['raw_label'])]
    # print("过滤掉最近没label的: %s" %(len(all_items)))
    analyse_1(items_has_label)
    analyse_2(items_has_label)
    analyse_3(items_has_label)
    analyse_4(items_has_label)
    analyse_5(all_items)
    return 
def main(path):
    with open(path, "r") as f:
        lines = f.readlines()
    # Use enumerate to get the round number
    for round, line in enumerate(lines):
        data = json.loads(line)
        # input(data['validate'][0])
        print(f"round_{round} start {data['start_at']}".center(100, '*'))
        analyse(round, data['validate'])
    return

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", type=str, required=True)  # 路径
    parser.add_argument('-s', '--stock', type=str, default=None) 
    parser.add_argument('-d', '--show-date', action='store_true')
    args = parser.parse_args()  # This should be parse_args()

    main(args.path)  # Use the parsed path argument