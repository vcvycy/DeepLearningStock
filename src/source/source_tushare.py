from source.source import Source
import tushare as ts
import sys
sys.path.append("..")
from common.context import Context
from common.stock_pb2 import *
from common.candle import Candle, Kline
import logging
from common.utils import *

class TushareSource(Source):
    def __init__(self, conf):
        super(TushareSource, self).__init__(conf)
        self.batch_size = conf.get("batch_size", 5)    # 一次返回多少context
        self.client = ts.pro_api(conf.get("api_key"))
        self.all_stocks = self.get_all_stocks()
        self.stock_size = self.all_stocks.shape[0]

        # 股票采样，生成context
        self.sample_recent_days = conf.get("sample_recent_days", 30)
        self.sample_min_train_days = conf.get("sample_min_train_days", 30)
        self.label_days = conf.get("label_days", 7)

        # 一次取多个context，保存在context_cache
        self.context_cache = []

        logging.error("TushareSource : stock size: %s" %(self.stock_size))
        logging.error(self.all_stocks)
        self.cursor = 0
        return 
    
    def get_all_stocks(self):
        # 拉取数据
        df = self.client.stock_basic(**{
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
    
    def load_kline_from_df(self, kline_df):
        # data frame -> proto::KLine
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
        return kline
    
    def get_kline_by_ts_code(self, ts_code):
        # 从tushare获取k线图
        df = self.client.daily(**{
            "ts_code": ts_code,
            "trade_date": "",
            "start_date": "",
            "end_date": "",
            "offset": "",
            "limit": ""
        }, fields=[
            "ts_code",
            "trade_date",
            "open",
            "high",
            "low",
            "close",
            "pre_close",
            "change",
            "pct_chg",
            "vol",
            "amount"
        ])
        # print(df)
        return self.load_kline_from_df(df)

    def update_context_cache(self):
        # cache还有数据，无须更新
        if len(self.context_cache) != 0:
            return 
        # 获取一个股票所有context: 股票进行采样
        if self.cursor >= self.stock_size:
            return 

        ts_code =  self.all_stocks.at[self.cursor, "ts_code"]
        
        contexts = []
        # 获取k线数据
        kline = self.get_kline_by_ts_code(ts_code)
        sub_ctx = {}
        for idx in range(self.label_days, len(kline)):
            # 从 [idx, ...] 作为训练数据,  [0.. idx] 作为label
            candle = kline[idx]       # 训练数据最后一个蜡烛
            context = Context("%s_%s" %(ts_code, candle.date))
            # stock pb数据  
            context.set("source.kline", Kline(kline.candles[idx:]))
            context.set("source.kline_label", Kline(kline.candles[:idx]))
            context.set("source.name", self.all_stocks.at[self.cursor, "name"])
            context.set("source.time_interval", TimeInterval.Day)  # 日线图
            context.set("source.ts_code", ts_code)
            context.set("source.train_date", candle.date)
            context.set("source.timestamp", str2timestamp(candle.date, "%Y%m%d"))
            contexts.append(context)
        self.cursor += 1
        self.context_cache = contexts
        return 
        
    def fetch_one_context(self):
        self.update_context_cache()
        if len(self.context_cache) == 0:
            return 
        context = self.context_cache[0]
        self.context_cache = self.context_cache[1:]
        return context

    # def fetch(self):
    #     # 获取股票数据
        
    #     return 

if __name__ == "__main__":
    # 只能在上一级目录测试
    pass