import json
import sys
import numpy as np
sys.path.insert(0, "../src/common")
from utils import read_parquet_or_jsonl, group_by_key, write_parquet_or_jsonl, mprint
def enum_each_model_run(path):
    def apply_rank(data):
        data['validate'].sort(key = lambda x : -x['pred'])
        for i, item in enumerate(data['validate']):
            item['rank'] = i + 1
        return 
    with open(path, "r") as f:
        lines = f.readlines()
    for line in lines: 
        try:
            data = json.loads(line)
            apply_rank(data)
            yield data
        except:
            pass
    return  


def topk_filter(date2items, topk = 5, days = 0):
    """
        如果某天的topk在前days天的topk出现，则不选
        如果数据太少，则过滤
    """
    dates = list(date2items)
    dates.sort(key=lambda x: int(x))
    need_filter_stock = list()
    items_filtered = []
    for  date in dates:
        items = date2items[date]
        if days > 0:
            need_filter_stock = need_filter_stock[-days*topk :]
        items.sort(key=lambda x: -x['pred'])
        topk_items = []
        for item in items:
            name = item['name']
            if len(topk_items) >= topk:
                break
            if name in need_filter_stock:
                continue
            topk_items.append(item)
            if days > 0:
                need_filter_stock.append(name)
        if len(topk_items) == topk:
            date2items[date] = topk_items
            items_filtered.extend(topk_items)
        else:
            print("删除%s的数据，数量太少, 过滤前 %s, 过滤后: %s" %(date, len(date2items[date]), len(topk_items)))
            del date2items[date]
    return date2items, items_filtered

def generate_topk_stock_by_date(date2items):
    all_stock_items = []
    dates = list(date2items)
    dates.sort(key=lambda x: -int(x))
    for date in dates:
        items = date2items[date]
        for i, item in enumerate(items):
            all_stock_items.append({
                "date": date,
                "Index": int(i),
                "rank" : item['rank'],
                "股票": item['name'],
                "预估收益": f(item['pred']),
                "真实收益": f(item['label']) if item['label'] is not None else '-'
            })
    return all_stock_items

def get_mean_per_day(date2items, key, func = np.mean):
    """ 每一天topk的均值
    """
    date2mean = {}
    for date in date2items:
        items = date2items[date]
        values = [item[key] for item in items]
        print(values)
        date2mean[date] = func(values)
    return date2mean
