import logging
import tushare as ts
import sys
sys.path.append("..")
from common.utils import *
from common.candle import Candle, Kline
from common.stock_pb2 import *
def TushareDecorator(fun):  # 装饰器, 用于retry(如qps超过上线会被切断)
    def wrapper(*args):
        retry = 3
        for i in range(retry):
            if i > 0:
                time.sleep(20)
            try:
                return fun(*args)
            except Exception as e:
                logging.error("[TushareApi-%s] exception: %s, retry: %s/%s, args: %s" %(fun.__name__, e, i+1, retry, args))
        raise Exception("[TushareApi] unknown failed")
    return wrapper
# Tushare的api封装
class TushareApi:
    @staticmethod
    def init_client(api_key):
        return ts.pro_api(api_key)
    # 获取所有股票
    @staticmethod
    def get_all_stocks(client):
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
        return df
    
    @staticmethod
    @TushareDecorator
    def get_kline_by_ts_code(client, ts_code, start_date = ""):
        # 从tushare获取k线图
        kline_df = client.daily(**{
            "ts_code": ts_code,
            "trade_date": "","start_date": start_date,
            "end_date": "","offset": "", "limit": ""
        }, fields=["ts_code","trade_date","open",
            "high","low","close","pre_close","change",
            "pct_chg","vol","amount"
        ])
        kline = Kline(ts_code) 
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

if __name__ == "__main__":
    client = TushareApi.init_client("009c49c7abe2f2bd16c823d4d8407f7e7fcbbc1883bf50eaae90ae5f")
    kline = TushareApi.get_kline_by_ts_code(client, "000001.SZ")
    print(kline)
    # kline.draw()
    print(kline.reduce("high", 360, "max"))
    for i in range(360):
        c = kline[i]
        print("%s %s" %(c.date, c.high))