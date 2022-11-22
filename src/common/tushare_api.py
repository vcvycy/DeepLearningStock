import logging
import tushare as ts
import sys
sys.path.append("..")
from common.utils import *
from common.candle import Candle, Kline
from common.stock_pb2 import *
def TushareDecorator(fun):  # 装饰器, 用于retry(如qps超过上线会被切断)
    def wrapper(*args, **kwargs):
        retry = 3
        for i in range(retry):
            if i > 0:
                time.sleep(20)
            try:
                return fun(*args, **kwargs)
            except Exception as e:
                logging.error("[TushareApi-%s] exception: %s, retry: %s/%s, args: %s" %(fun.__name__, e, i+1, retry, args))
        raise Exception("[TushareApi] unknown failed")
    return wrapper

client = ts.pro_api("009c49c7abe2f2bd16c823d4d8407f7e7fcbbc1883bf50eaae90ae5f")
# Tushare的api封装
class TushareApi:
    __ts_code2name = {}
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
    @staticmethod
    def get_all_stocks(client, to_dict = False):
        global __ts_code2name
        # 拉取数据
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
        for idx,value in df.iterrows():
            TushareApi.__ts_code2name[value["ts_code"]] = value["name"]
        if to_dict:
            return [value.to_dict() for idx,value in df.iterrows()]
        else:
            return df
    
    @staticmethod
    @TushareDecorator
    def get_kline_by_ts_code(client, ts_code, start_date = "", end_date = ""):
        # 从tushare获取k线图
        kline_df = client.daily(**{
            "ts_code": ts_code,
            "trade_date": "","start_date": start_date,
            "end_date": end_date,"offset": "", "limit": ""
        }, fields=["ts_code","trade_date","open",
            "high","low","close","pre_close","change",
            "pct_chg","vol","amount"
        ])
        kline = Kline(ts_code = ts_code) 
        for i in range(kline_df.shape[0]):
            c = Candle()
            df2candle_attr = {    # dataframe的名字映射到canlde的名字中
                "high" : "high",
                "low" : "low", 
                "open" : "open", 
                "close" : "close", 
                "pre_close" : "pre_close", 
                "high" : "high", 
                "trade_date" : "date",
                "vol" : "vol",
                "amount" : "amount"
            }
            for df_attr in df2candle_attr:
                candle_attr = df2candle_attr[df_attr]
                setattr(c, candle_attr, kline_df.at[i, df_attr])
            kline.add(c) 
        return kline 
    @staticmethod
    @TushareDecorator
    def get_ts_code2basic(ts_code):
        global client
        if len(TushareApi.ts_code2basic) == 0:
            date = timestamp2str(int(time.time()), format = "%Y%m%d") 
            df = client.query('daily_basic', ts_code='', trade_date=date,fields='ts_code,trade_date,turnover_rate,turnover_rate_f,total_mv,circ_mv,volume_ratio,pe,pb') 
            arr = [value.to_dict() for idx,value in df.iterrows()] 
            TushareApi.ts_code2basic = {x["ts_code"] : x for x in arr}
        return TushareApi.ts_code2basic[ts_code]
    # @staticmethod
    # @TushareDecorator
    # def get_kline_by_ts_code_v2(client, ts_code, start_date = "", end_date = ""):
if __name__ == "__main__":
    # print(ts.pro_bar(ts_code='688699.SH', adj='qfq', start_date='20220809', end_date='20221011'))
    client = TushareApi.init_client("009c49c7abe2f2bd16c823d4d8407f7e7fcbbc1883bf50eaae90ae5f")
    # print(TushareApi.get_all_stocks(client))
    # print(len([s for s in TushareApi.get_all_stocks(client, to_dict = True) if s["ts_code"][0] == '8']))

    basic = TushareApi.get_ts_code2basic("000838.SZ")
    print(type(basic["pe"]))
    import math
    print(math.isnan(basic["pe"]))

    # for stock in  TushareApi.get_all_stocks(client, to_dict = True):
    #     if stock["name"] == "明微电子":
    #         print(stock)
    #         break
    # # print(TushareApi.get_name("688737.SH"))
    # kline = TushareApi.get_kline_by_ts_code(client, "688699.SH", end_date="20221011")
    # kline = TushareApi.get_kline_by_ts_code(client, "000007.SZ", end_date="")
    # print(len(kline))
    # print(kline.median_price_estimator(14))
    # for c in kline:
    #     # if c.date == "20221011":
    #     print(c)
    #     break
    # print(kline.get_rise(30))
    # print(kline[0].close)
    # print(kline[30].pre_close)
    # kline.draw()
    # print(kline.reduce("high", 360, "max"))
    # print(kline.name)
    # print(kline.ts_code)
    # for i in range(360):
    #     c = kline[i]
    #     print("%s %s" %(c.date, c.high))