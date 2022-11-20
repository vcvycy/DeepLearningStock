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
from common.tushare_api import *
# Tushare Source
class TushareSource(MultiThreadSource):
    def __init__(self, conf):
        super(TushareSource, self).__init__(conf)
        # 常规配置
        self.conf = conf
        self.batch_size = conf.get("batch_size", 5)    # 一次返回多少context
        # 初始化tushare client
        self.client = TushareApi.init_client(conf.get("api_key"))

        self.sample_recent_days = conf.get("sample_recent_days", 9999)        # 采样最近N天
        self.sample_min_train_days = conf.get("sample_min_train_days", 10)  #
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
            start_date = self.conf.get("start_date")
            ts_code = self.all_stocks.at[stock_idx, "ts_code"]
            kline = TushareApi.get_kline_by_ts_code(self.client, ts_code, start_date)  
            ctx_num = 0  
            # 至少有lable_days天作为Label，所以这几天不采样训练数据
            for idx in range(len(kline)):
                if ctx_num >= self.sample_recent_days:
                    break
                if len(kline) - idx < self.sample_min_train_days:
                    break
                # 从 [idx, ...] 作为训练数据,  [0.. idx] 作为label
                candle = kline[idx]       # 训练数据最后一个蜡烛
                context = Context("%s_%s" %(ts_code, candle.date))
                # stock pb数据  
                context.set("source.kline", Kline(ts_code = kline.ts_code, candles = kline.candles[idx:]))
                context.set("source.kline_label", Kline(ts_code = kline.ts_code, candles = kline.candles[:idx]))
                context.set("source.name", self.all_stocks.at[stock_idx, "name"])
                context.set("source.time_interval", TimeInterval.Day)  # 日线图
                context.set("source.ts_code",  ts_code)
                context.set("source.train_date", candle.date)
                context.set("source.timestamp", str2timestamp(candle.date, "%Y%m%d"))
                self.add_context(context) 
                ctx_num += 1
        except Exception as e:
            print("exp: %s" %(e))
        self.thread_finish_num +=1 
        return ctx_num

    def start_multi_thread(self):
        # self.stock_size = 5
        for i in range(self.stock_size):
            self.add_thread(TushareSource.gen_contexts_thread_fun, i) 
        return 
