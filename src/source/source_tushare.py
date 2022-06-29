from source.source import Source
import tushare as ts
import sys
sys.path.append("..")
from common.context import Context
from common.stock_pb2 import *
import logging

class TushareSource(Source):
    def __init__(self, conf):
        super(TushareSource, self).__init__(conf)
        self.batch_size = conf.get("batch_size", 5)    # 一次返回多少context
        self.client = ts.pro_api(conf.get("api_key"))
        self.all_stocks = self.get_all_stocks()
        self.stock_size = self.all_stocks.shape[0]
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
    def get_tushare_kline(self, ts_code):
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
        return df
    def load_kline_from_df(self, kline_df):
        # data frame -> proto::KLine
        candles = []
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
            candles.append(c)
        return candles
    def fetch_one_context(self):
        if self.cursor >= self.stock_size:
            return None

        ts_code =  self.all_stocks.at[self.cursor, "ts_code"]
        # 创建context
        stock_id = self.all_stocks.at[self.cursor, "symbol"]
        context = Context(ts_code)
        # stock pb数据
        # 获取k线数据
        kline_df = self.get_tushare_kline(ts_code)
        candles = self.load_kline_from_df(kline_df)
        context.set("source.kline", candles)
        context.set("source.name", self.all_stocks.at[self.cursor, "name"])
        context.set("source.time_interval", TimeInterval.Day)  # 日线图
        context.set("source.ts_code", ts_code)
        context.set("source.ipo_time", self.all_stocks.at[self.cursor, "list_date"])
        self.cursor += 1
        return context
    def fetch(self):
        # 获取股票数据
        
        return 

if __name__ == "__main__":
    
    logger = logging.getLogger(__name__)  
    logger.setLevel(logging.WARNING)
    handler = logging.FileHandler('/Users/bytedance/DeepLearningStock/my.log')
    formatter = logging.Formatter('%(asctime)s : %(name)s  : %(funcName)s : %(levelname)s : %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    conf = {
        "batch_size" : 1,
        "apikey" : "e2d615dd1d6a00f48b84eb43f2aa64a413c190b7295a6ab6729df2a5"
    } 
    tushare = TushareSource(conf)
    print(tushare.fetch_one())
    # print(tushare.fetch_one())