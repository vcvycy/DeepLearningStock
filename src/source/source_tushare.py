from source.source import Source
import tushare as ts
import sys
sys.path.append("..")
from common.context import Context
from common.stock_pb2 import *
from common.candle import Candle, Kline
import logging
from common.utils import *
import random

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
    def get_kline_by_ts_code(client, ts_code):
        # 从tushare获取k线图
        kline_df = client.daily(**{
            "ts_code": ts_code,
            "trade_date": "","start_date": "20220101",
            "end_date": "","offset": "", "limit": ""
        }, fields=["ts_code","trade_date","open",
            "high","low","close","pre_close","change",
            "pct_chg","vol","amount"
        ])
        # kline_df = client.daily(ts_code=ts_code, start_date='20180701', end_date='20180718')

        kline = Kline() 
        for i in range(kline_df.shape[0]):
            c = Candle()
            c.high = kline_df.at[i, "high"]
            c.low = kline_df.at[i, "low"]
            c.open = kline_df.at[i, "open"]
            c.close = kline_df.at[i, "close"]
            c.pre_close = kline_df.at[i, "pre_close"]
            c.high = kline_df.at[i, "high"]
            c.date = kline_df.at[i, "trade_date"]
            c.vol = kline_df.at[i, "vol"]
            c.amount = kline_df.at[i, "amount"]
            kline.add(c)
        print("[get_kline_by_ts_code]%s kline %s" %(ts_code, kline[0]))
        return kline 

class TushareSource(Source):
    def __init__(self, conf):
        super(TushareSource, self).__init__(conf)
        # 常规配置
        self.batch_size = conf.get("batch_size", 5)    # 一次返回多少context
        self.sample_recent_days = conf.get("sample_recent_days", 30)
        self.sample_min_train_days = conf.get("sample_min_train_days", 30)
        self.label_days = conf.get("label_days", 7)

        # 初始化tushare client
        self.client = TushareApi.init_client(conf.get("api_key"))

        # 获取所有股票数据
        self.all_stocks = TushareApi.get_all_stocks(self.client)
        self.stock_size = self.all_stocks.shape[0]
        logging.error("TushareSource : stock size: %s" %(self.stock_size))
        logging.error(self.all_stocks)
        self.total_context = 0 
        
        # 
        self.init_thread_pool()
        return

    @staticmethod
    def gen_contexts_thread_fun(tushare_src_obj, ts_code):
        # 获取k线数据
        kline = TushareApi.get_kline_by_ts_code(tushare_src_obj.client, ts_code)  
        # print("(gen_contexts_thread_fun) %s" %(kline[0]))
        ctx_num = 0
        # for idx in range(self.label_days, len(kline)):
        #     if ctx_num >= self.sample_recent_days:
        #         break
        #     # 从 [idx, ...] 作为训练数据,  [0.. idx] 作为label
        #     candle = kline[idx]       # 训练数据最后一个蜡烛
        #     context = Context("%s_%s" %(ts_code, candle.date))
        #     # stock pb数据  
        #     context.set("source.kline", Kline(kline.candles[idx:]))
        #     context.set("source.kline_label", Kline(kline.candles[:idx]))
        #     context.set("source.name", self.all_stocks.at[self.cursor, "name"])
        #     context.set("source.time_interval", TimeInterval.Day)  # 日线图
        #     context.set("source.ts_code", ts_code)
        #     context.set("source.train_date", candle.date)
        #     context.set("source.timestamp", str2timestamp(candle.date, "%Y%m%d"))
        #     tushare_src_obj.add_context(context) 

        #     ctx_num += 1
        print("%s -> %s %s" %(ts_code, ctx_num, len(kline)))
        return ctx_num

    def init_thread_pool(self):
        print("init_thread_pool") 
        self.stock_size = 5
        for i in range(self.stock_size):
            ts_code =  self.all_stocks.at[i, "ts_code"]
            self.add_thread(TushareSource.gen_contexts_thread_fun, ts_code) 
        

#     def update_context_cache(self):
#         # cache还有数据，无须更新
#         if len(self.context_cache) != 0:
#             return 
#         # 获取一个股票所有context: 股票进行采样
#         if self.cursor >= self.stock_size:
#             return 

#         ts_code =  self.all_stocks.at[self.cursor, "ts_code"]
        
#         contexts = []
#         return 
        
#     def get_context(self):
#         self.update_context_cache()
#         if len(self.context_cache) == 0:
#             return 
#         context = self.context_cache[0]
#         self.context_cache = self.context_cache[1:]
#         return context

#     def thread_pool_init(self):
#         return 
# if __name__ == "__main__":
#     # 只能在上一级目录测试
#     pass