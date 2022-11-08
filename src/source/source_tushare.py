from source.source import Source, MultiThreadSource
import tushare as ts
import sys
sys.path.append("..")
from common.context import Context
from common.stock_pb2 import *
from common.candle import Candle, Kline
import logging
from common.utils import *
import random
import time

def TushareDecorator(fun):  # 装饰器, 用于retry(如qps超过上线会被切断)
    def wrapper(*args):
        retry = 3
        for i in range(retry):
            try:
                return fun(*args)
            except Exception as e:
                logging.error("[TushareApi-%s] exception: %s, retry: %s/%s" %(fun.__name__, e, i, retry))
                time.sleep(1)
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
    def get_kline_by_ts_code(client, ts_code):
        # 从tushare获取k线图
        kline_df = client.daily(**{
            "ts_code": ts_code,
            "trade_date": "","start_date": "",
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

# Tushare Source
class TushareSource(MultiThreadSource):
    def __init__(self, conf):
        super(TushareSource, self).__init__(conf)
        # 常规配置
        self.conf = conf
        self.batch_size = conf.get("batch_size", 5)    # 一次返回多少context
        # 初始化tushare client
        self.client = TushareApi.init_client(conf.get("api_key"))

        self.sample_recent_days = conf.get("sample_recent_days", 30)        # 采样最近N天
        self.sample_min_train_days = conf.get("sample_min_train_days", 10)  # 
        self.label_days = conf.get("label_days", 7)
        # 获取所有股票数据
        self.all_stocks = TushareApi.get_all_stocks(self.client)
        self.stock_size = self.all_stocks.shape[0]
        logging.error("TushareSource : stock size: %s" %(self.stock_size))
        logging.error(self.all_stocks)
        self.total_context = 0 
        
        # 
        self.start_multi_thread()
        return

    def gen_contexts_thread_fun(self, stock_idx):
        # 多线程入口函数
        try:
            ts_code = self.all_stocks.at[stock_idx, "ts_code"]
            kline = TushareApi.get_kline_by_ts_code(self.client, ts_code)  
            ctx_num = 0  
            # 至少有lable_days天作为Label，所以这几天不采样训练数据
            for idx in range(self.label_days, len(kline)):
                if ctx_num >= self.sample_recent_days:
                    break
                # 从 [idx, ...] 作为训练数据,  [0.. idx] 作为label
                candle = kline[idx]       # 训练数据最后一个蜡烛
                context = Context("%s_%s" %(ts_code, candle.date))
                # stock pb数据  
                context.set("source.kline", Kline(kline.name, kline.candles[idx:]))
                context.set("source.kline_label", Kline(kline.name, kline.candles[:idx]))
                context.set("source.name", self.all_stocks.at[stock_idx, "name"])
                context.set("source.time_interval", TimeInterval.Day)  # 日线图
                context.set("source.ts_code",  ts_code)
                context.set("source.train_date", candle.date)
                context.set("source.timestamp", str2timestamp(candle.date, "%Y%m%d"))
                self.add_context(context) 
                ctx_num += 1
        except Exception as e:
            print("exp: %s" %(e))
            exit(0)
        return ctx_num

    def start_multi_thread(self):
        # self.stock_size = 5
        for i in range(self.stock_size):
            self.add_thread(TushareSource.gen_contexts_thread_fun, i) 
        return 
