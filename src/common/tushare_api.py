import logging
import tushare as ts
import sys
sys.path.append("..")
from common.utils import *
from common.candle import Candle, Kline
from common.stock_pb2 import *
import math
import time
import os
def TushareDecorator(fun):  # 装饰器, 用于retry(如qps超过上线会被切断)
    def wrapper(*args, **kwargs):
        retry = 6
        for i in range(retry):
            if i > 0:
                time.sleep(20)
            try:
                return fun(*args, **kwargs)
            except Exception as e:
                logging.error("[TushareApi-%s] exception: %s, retry: %s/%s, args: %s" %(fun.__name__, e, i+1, retry, args))
                if "抱歉，您每分钟最多访问该接口200次" in str(e):
                    time.sleep(10)
                else:
                    time.sleep(1)
        # 如果6次都失败则跑到这里
        raise Exception("[TushareApi] 重试%s次仍未成功 exit" %(retry))
        os._exit()
    return wrapper

client = ts.pro_api("009c49c7abe2f2bd16c823d4d8407f7e7fcbbc1883bf50eaae90ae5f")
# Tushare的api封装
class TushareApi:
    __ts_code2name = {}
    __ts_code2type = {}
    ts_code2basic = {}
    @staticmethod
    def init_client(api_key):
        global client
        return client
    # 获取所有股票
    def get_name(ts_code): 
        if len(TushareApi.__ts_code2name) == 0:
            TushareApi.get_all_stocks()
        return TushareApi.__ts_code2name[ts_code]
    def is_etf(ts_code):
        return TushareApi.__ts_code2type[ts_code] == "etf"
    @staticmethod
    def get_all_stocks():
        global client
        global __ts_code2name
        data = []
        # 基金etf/lof
        df = client.fund_basic(market='E', status='L') 
        for idx,value in df.iterrows():
            if value["list_date"] is not None and  value["list_date"] > "20220101":   # 基金只去2022前发行的，有足够的数据训练
                continue
            data.append({
                "ts_code" : value["ts_code"],
                "name" : value["name"],
                "category" : "etf"
            })
            TushareApi.__ts_code2type[value["ts_code"]] = "etf"
        print("基金总数 %s, 过滤后剩下: %s" %(df.shape[0], len(data)))
        # 拉取股票数据
        df = client.stock_basic(**{
            "ts_code": "",
            "name": "",
            "exchange": "",
            "market": "",
            "is_hs": "",
            "list_status": "L",
            "limit": "",
            "offset": ""
        }, fields=[
            "ts_code",
            "symbol",
            "name",
            "area",
            "industry",
            "market",
            "list_date"
        ])
        # print(df)
        for idx,value in df.iterrows():
            data.append({
                "ts_code" : value["ts_code"],
                "name" : value["name"],
                "category" : "stock"
            })
            TushareApi.__ts_code2type[value["ts_code"]] = "stock"
        # 指数
        df = client.index_basic(market = "SSE")
        for idx,value in df.iterrows(): 
            TushareApi.__ts_code2type[value["ts_code"]] = "index"
        return data 
    
    @staticmethod
    @TushareDecorator
    def get_kline_by_ts_code_weekly(ts_code, start_date = "", end_date = ""):
        global client
        def update_kline(kline, kline_df):
            for i in range(kline_df.shape[0]):
                c = Candle(
                    date = kline_df.at[i, "trade_date"],
                    open = kline_df.at[i, "open"],
                    high = kline_df.at[i, "high"],
                    low = kline_df.at[i, "low"],
                    close = kline_df.at[i, "close"],
                    pre_close = kline_df.at[i, "pre_close"],
                    amount = kline_df.at[i, "amount"],
                    vol = kline_df.at[i, "vol"]
                ) 
                kline.add(c)
            return 
        kline = Kline(ts_code = ts_code) 
        if TushareApi.__ts_code2type[ts_code] == "stock":
            kline_df =  client.weekly(ts_code=ts_code, start_date=start_date, end_date=end_date, 
                                    fields='ts_code,trade_date,pre_close,open,high,low,close,vol,amount')
            update_kline(kline, kline_df)
        return kline
    @staticmethod
    @TushareDecorator
    def get_kline_by_ts_code(ts_code, start_date = "", end_date = ""):
        def update_kline(kline, kline_df, basic_df = None):
            for i in range(kline_df.shape[0]):
                c = Candle(
                    date = kline_df.at[i, "trade_date"],
                    open = kline_df.at[i, "open"],
                    high = kline_df.at[i, "high"],
                    low = kline_df.at[i, "low"],
                    close = kline_df.at[i, "close"],
                    pre_close = kline_df.at[i, "pre_close"],
                    amount = kline_df.at[i, "amount"],
                    vol = kline_df.at[i, "vol"]
                ) 
                if basic_df is not None:
                    assert basic_df.at[i, "trade_date"] == kline_df.at[i, "trade_date"]
                    basic_attr = "turnover_rate,turnover_rate_f,total_mv,circ_mv,volume_ratio,pe,pb".split(",")
                    for k in basic_attr: 
                        value = basic_df.at[i, k]
                        if value is None or math.isnan(value):
                            if k == "turnover_rate_f":
                                value = basic_df.at[i, "turnover_rate"] * basic_df.at[i, "total_mv"] / basic_df.at[i, "circ_mv"]
                        setattr(c, k, value) 
                kline.add(c)
            return 
        global client
        kline = Kline(ts_code = ts_code) 
        # 从tushare获取k线图: 未复权
        # 前复权
        if TushareApi.__ts_code2type[ts_code] == "stock":
            # kline_df = client.daily(**{
            #     "ts_code": ts_code,
            #     "trade_date": "","start_date": start_date,
            #     "end_date": end_date,"offset": "", "limit": ""
            # }, fields=["ts_code","trade_date","open",
            #     "high","low","close","pre_close","change",
            #     "pct_chg","vol","amount"
            # ])
            kline_df = ts.pro_bar(ts_code=ts_code, adj='qfq', start_date=start_date, end_date=end_date) #前复权
            fields = 'ts_code,trade_date,turnover_rate,turnover_rate_f,total_mv,circ_mv,volume_ratio,pe,pb'
            basic_df = client.query('daily_basic', ts_code=ts_code, start_date=start_date, end_date=end_date, fields=fields)
            # print(basic_df)
            update_kline(kline, kline_df, basic_df)
            # 换手率等数据 
        elif TushareApi.__ts_code2type[ts_code] == "etf":
            time.sleep(1)
            kline_df = client.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            update_kline(kline, kline_df)
        elif TushareApi.__ts_code2type[ts_code] == "index":  # 指数
            kline_df = client.index_daily(ts_code=ts_code, start_date = start_date)
            update_kline(kline, kline_df)
        else:
            raise Exception("unknow ts_code: %s" %(ts_code))
        return kline 
    @staticmethod
    @TushareDecorator
    def get_basic_by_ts_code(ts_code, start_date = "", end_date = ""):
        global client
        fields = 'ts_code,trade_date,turnover_rate,turnover_rate_f,total_mv,circ_mv,volume_ratio,pe,pb'
        df = client.query('daily_basic', ts_code=ts_code, start_date=start_date, end_date=end_date, fields=fields)
        return df
    @staticmethod
    @TushareDecorator
    def get_ts_code2basic(ts_code, timestamp = time.time()):
        global client
        fields = 'ts_code,trade_date,turnover_rate,turnover_rate_f,total_mv,circ_mv,volume_ratio,pe,pb'
        if len(TushareApi.ts_code2basic) == 0:
            date = timestamp2str(timestamp, format = "%Y%m%d") 
            df = client.query('daily_basic', ts_code='', trade_date=date,fields=fields) 
            arr = [value.to_dict() for idx,value in df.iterrows()] 
            if len(arr) == 0:  # 节假日等, 取前一天数据
                return TushareApi.get_ts_code2basic(ts_code, timestamp - 86400)
            TushareApi.ts_code2basic = {x["ts_code"] : x for x in arr}
        if ts_code not in TushareApi.ts_code2basic:
            # 可能原因: 当前为停牌状态, 导致今日的数据没有
            df = client.query('daily_basic', ts_code=ts_code, trade_date='', fields=fields)
            for idx,value in df.iterrows():
                TushareApi.ts_code2basic[ts_code] = value.to_dict()
                break
        return TushareApi.ts_code2basic[ts_code]
def init():
    TushareApi.get_all_stocks()
init()
if __name__ == "__main__": 
    # client = TushareApi.init_client("009c49c7abe2f2bd16c823d4d8407f7e7fcbbc1883bf50eaae90ae5f") 
    # client.fund_basic(market='E') 
    
    # TushareApi.get_basic_by_ts_code("000001.SZ", start_date= "20200101")
    # TushareApi.get_basic_by_ts_code("513050.SH", start_date= "20200101")
    # kline = TushareApi.get_kline_by_ts_code("300711.SZ", start_date= "20200601", end_date="")
    # print(len(kline))
    # print(kline)
    # print(kline.get_ma_reverse_times(k = 30))
    kline = TushareApi.get_kline_by_ts_code_weekly("000001.SZ", start_date= "20100601", end_date="")
    print(kline[0])
    # print(kline.reduce("close", 30, "ma"))
    # print(kline[0])
    # print(kline[1])
    # print(kline.get_ma_reverse_times(k = 30))
    # print(len(kline))
    # print(kline)
    # for i in range(100):
    #     print("%s %s" %(kline[i].date, kline.get_macd(i)))
    # for i in kline:
    #     print(i)
    # kline.draw()
    # for item in TushareApi.get_all_stocks():
    #     if "000001" in item["ts_code"]:
    #         print(item)
    # kline = TushareApi.get_kline_by_ts_code("513050.SH", start_date="", end_date = '20221212')
    # kline.draw() 