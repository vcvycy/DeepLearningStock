import bottle
import glob  # Added glob to import for file pattern matching
import json  # Added json for JSON processing
import numpy as np  # Added numpy for mean calculations
import os 
# Assuming these are your utility functions
import sys 
import functools
import math
import logging
from parse_model_json import *
sys.path.insert(0, "../src/common")
sys.path.insert(0, "../src")
from tushare_api import TushareApi
from utils import read_parquet_or_jsonl, group_by_key, write_parquet_or_jsonl, mprint

@bottle.route("/<path>")
def files(path):
    print("请求访问文件: %s" %(path))
    if os.path.exists(path):
        content = open(path, "rb") 
        return content.read()
    else:
        # print "not exist :%s" %(path)
        return "empty"

@bottle.route('/model_list')
def model_list():
    # Using glob.glob to return file paths that match a specified pattern
    paths = glob.glob("../log/result.json.*")
    paths.sort(key = lambda x : x)
    paths = paths[::-1]
    return json.dumps(paths)

def analyse(all_items, topk = 5, dedup = False):
    def get_topk_per_day(date2items, n = 7):
        # 如果某天的topk在前n天的topk出现，则不选
        dates = list(date2items)
        dates.sort(key=lambda x: int(x))
        need_filter_stock = list()
        for  date in dates:
            items = date2items[date]
            need_filter_stock = need_filter_stock[-n*topk :]
            items.sort(key=lambda x: -x['pred'])
            topk_items = []
            for item in items:
                name = item['name']
                if len(topk_items) >= topk:
                    break
                if name in need_filter_stock:
                    continue
                topk_items.append(item)
                if dedup:
                    need_filter_stock.append(name)
            date2items[date] = topk_items
        date2items = {date :date2items[date] for date in date2items if len(date2items[date]) >= topk}
        return date2items
    def f(x):
        return "%.2f%%" % (100 * x)

    all_items.sort(key=lambda x: -x['pred'])

    date2items = group_by_key(all_items, "date")
    ##### 获取每天的topk个股票: 并根据dedup决定是否进行消重 ####
    date2items = get_topk_per_day(date2items)   
    dates = list(date2items)
    dates.sort(key=lambda x: -int(x))
    csv_data = []
    avg_return = []   # 每天的平均return 
    avg_pred = []
    date2rank = {}
    date2count = {}
    for date in dates:
        items = date2items[date]
        date2count[date] = len(items)
        for i, item in enumerate(items):
            csv_data.append({
                "date": date,
                "Index": int(i),
                "rank" : item['rank'],
                "股票": item['name'],
                "置信度" : item['certainly'],
                "预估收益": item['pred'],
                "真实收益": item['label'] if item['label'] is not None else '-'
            })
        # Calculate the mean of predictions and labels if available
        avg_pred_value = np.mean([item['pred'] for item in items])
        avg_label_value = np.mean([item['label'] for item in items if item['label'] is not None])
        avg_rank_value = np.mean([item['rank'] for item in items])
        date2rank[date] = avg_rank_value
        csv_data.append({
            "date": date,
            "股票": "平均值",
            "预估收益": avg_pred_value,
            "真实收益": avg_label_value if items[0]['label'] is not None else "",
        })
        avg_pred.append(avg_pred_value)
        if items[0]['label'] is not None:
            avg_return.append(avg_label_value)
    # Write data to a file or print it - replace these with your actual functions if they differ
    # write_parquet_or_jsonl(csv_data, "1.csv")
    # mprint(csv_data)
    return dates, avg_return, date2rank, avg_pred, date2count, csv_data

# # 定义装饰器
# def decorator_get_method(func):
#     def wrapper(*args, **kwargs):
#         # 获取GET请求的所有参数，将它们作为kwargs传递
#         query_params = bottle.request.query.decode()
#         kwargs.update(query_params)
#         return func(*args, **kwargs)
#     return wrapper


# 定义装饰器
def decorator_post_method(func):
    # 请求; byte-X POST -H "Content-Type: application/json" -d '{"key1": "value1", "key2": "value2"}' http://localhost:8080/submit
    def wrapper(*args, **kwargs):
        # 根据请求的内容类型解析POST数据
        if bottle.request.content_type.startswith('application/json'):
            # 尝试解析JSON数据
            try:
                data = bottle.request.json
            except json.JSONDecodeError:
                return HTTPResponse(status=400, body='Invalid JSON')
        else:
            # 默认为表单数据
            data = bottle.request.forms.decode()

        # 更新kwargs
        kwargs.update(data)
        return func(*args, **kwargs)
    return wrapper

# 应用装饰器到路由上
# @bottle.route('/hello')
# @decorator_get_method
# def hello(**kwargs):
#     # 现在所有的GET参数都在kwargs字典里
#     name = kwargs.get('name', 'World')
#     return f'Hello, {name}!'


# # 应用装饰器到路由上
# @bottle.post('/submit')
# @decorator_post_method
# def submit(**kwargs):
#     # 现在所有的POST参数都在kwargs字典里
#     # ...处理逻辑...
    
#     return f'Received: {json.dumps(kwargs)}'


def get_classify_analyse(items, topk, dedup):
    def enum_classify_items(items):
        tscode2cate = TushareApi.get_stock2classify()
        all_stock = TushareApi.get_all_stocks()
        name2cate = {}
        for tscode in tscode2cate:
            classifies = tscode2cate[tscode]
            if len(classifies) <= 0:
                continue
            if len(classifies) > 1:
                print("股票%s有多个分类 %s, 只取1个!" %(tscode, classifies))
            classify = classifies[0]
            name = TushareApi.get_name(tscode)
            name2cate[name] = classify
        print("有分类的股票数: %s" %(len(name2cate)))
        classify2items = {} 
        for item in items:
            name = item['name']
            if name not in name2cate:
                continue
            classify = name2cate[name]
            if classify not in classify2items:
                classify2items[classify] = []
            classify2items[classify].append(item) 
        for classify in classify2items:
            stocks = list(set([item['name'] for item in classify2items[classify]]))
            yield classify, stocks, classify2items[classify]
        return 

    results = []
    flatten = lambda dates, date2xx : [date2xx.get(date, 0) for date in dates]
    for category, stocks, cur_items in enum_classify_items(items):
        days, return_per_day, date2rank, pred_per_day, date2count,  top5_stock_per_day =  analyse(cur_items, topk=topk, dedup = dedup)  # Removed round as it seemed out of context
        if len(top5_stock_per_day) < topk:
            continue
        topk_avg_pred = np.mean([item['预估收益'] for item in top5_stock_per_day[:topk]])
        result = {
            "stocks" : list(stocks),
            "stock_size" : len(stocks),
            "category" : category,
            "count" : len(cur_items), 
            "recommend_top_stock" : top5_stock_per_day[:topk],
            "return_all" : np.mean(return_per_day) if len(return_per_day) > 0 else -1,
            "return_p50" : np.percentile(return_per_day, 50) if len(return_per_day) > 0 else -1,
            "tokp_avg_pred" : topk_avg_pred,
        } 
        results.append(result)  
    results.sort(key = lambda x : - x['tokp_avg_pred'])
    return results


@bottle.post("/merge_results")
@decorator_post_method
@functools.lru_cache(maxsize=None)  # 无限缓存
def merge_results(path, **kwargs):
    from result_reader import merge
    print("merge多个模型: %s" %(path))
    if path.endswith(".merged") or os.path.exists(path+".merged"):
        return "模型已经合并过了"
    save_path = merge(path)
    return {"save_path" : save_path}

@bottle.post("/model_result_process")
@decorator_post_method
@functools.lru_cache(maxsize=None)  # 无限缓存
def model_result_process(path, topk = 5, dedup = True, min_certainly = 0, **kwargs):
    topk = int(topk)
    print("path= %s topk= %s dedup = %s" %(path, topk, dedup))
    # Ensure that 'path' is provided
    if not path:
        response.status = 400
        return "Missing 'path' parameter."
    
    with open(path, "r") as f:
        lines = f.readlines()
    result = []
    for line in lines:
        data = json.loads(line)
        validate_items = data['validate']
        validate_items.sort(key = lambda x : -x['pred'])
        ## filter validate_items
        validate_items = [item for item in validate_items if item['certainly'] > float(min_certainly)]
        if len(validate_items) == 0:
            continue
        for i, item in enumerate(validate_items):
            item['rank'] = i + 1
        days, return_per_day, date2rank, pred_per_day, date2count,  top5_stock_per_day =  analyse(validate_items, topk=topk, dedup = dedup)  # Removed round as it seemed out of context
        flatten = lambda dates, date2xx : [date2xx.get(date, 0) for date in dates]
        single_result = {
            "summary" : {
                "date_num" : len(days),
                "date_num_with_return" : len(return_per_day),
                "return_all" : np.mean(return_per_day) if len(return_per_day) > 0 else -1,
                "return_p50" : np.percentile(return_per_day, 50) if len(return_per_day) > 0 else -1,
                "count" : len(validate_items)
            },
            "backtest": top5_stock_per_day,
            "days" : days,
            "return_per_day" : [0] * (len(days) - len(return_per_day)) + return_per_day, # 没有return的，补0
            "rank_per_day" : flatten(days, date2rank),
            "pred_per_day" : pred_per_day,
            "count_per_day" : flatten(days, date2count),
            "classify" : get_classify_analyse(validate_items, topk = topk, dedup = dedup)

        }
        result.append(single_result)

    # Here you need to define what you want to do with the result
    # For example, returning it as JSON:
    return json.dumps(result, ensure_ascii=False, indent=2)

def test():
    # get_classify_analyse
    # model_result_process('../log/result.json.20240228_2345')
    model_result_process("../log/result.json.20240227_1814")
    exit(0)
# test()


@bottle.route("/")
def index():
    return open("index.html").read()

# Finally, you need to run the bottle server
bottle.run(host='localhost', port=8080)