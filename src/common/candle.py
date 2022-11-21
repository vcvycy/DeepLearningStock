
import sys
sys.path.append("..")
from common.stock_pb2 import *
import pandas as pd
import mplfinance as mpf 
from common.utils import *
import numpy as np
import logging

class Candle(): 
    CommonAttr = [
        "time", "open", "high", "low", "close", "amount", "vol", "turnover", "pre_close", "date"
    ]
    def __init__(self):
        # super(Candle, self).__init__()
        for attr in Candle.CommonAttr:
            setattr(self, attr, None) 
        return 
    def __str__(self):
        s = ""
        for attr in Candle.CommonAttr:
            if getattr(self, attr) is not None:
                s +="%s: %s, " %(attr, getattr(self, attr))
        return s

    def __repr__(self):
        return self.__str__()

    def get_rise(self):
        return self.close / self.pre_close -1

class Kline():
    def __init__(self, ts_code = "unknown", candles = []):
        self.ts_code = ts_code
        self.name = ts_code
        self.candles = [] 
        for c in candles:
            self.add(c)
    
    def add(self, candle):
        self.candles.append(candle)
        return 
    
    def get_rise(self, days = 1):
        """
          获取k线图 days天的涨跌幅
        """
        if days >= len(self):
            days = len(self) - 1
        open = self.candles[days].close
        close = self.candles[0].close
        return close/open - 1
    
    def __getitem__(self, idx):
        return self.candles[idx]
    
    def at(self, idx):
        return self.candles[idx]

    def __len__(self):
        return len(self.candles)

    def __repr__(self):
        return self.__str__()
    def __str__(self):
        rsp = "[KLine %s]\n    " %(self.name)
        if len(self) > 10:
            rsp += str(self.candles[:2]) + "..." + str(self.candles[-2:])
        else: 
            rsp += str(self.candles)
        return rsp
    def draw(self, volume = True, mav=(7,30, 120), savefig=None, max_days= 90):
        """
        画k线图，data格式为
        [
        {
            "Date" : timestamp,
            "Open" : 100,
            "Close" : 
        }
        ]
        """
        data = [
            {
                "Date" : str2timestamp(c.date, "%Y%m%d"),
                "Open" : c.open,
                "High" : c.high,
                "Low" : c.low,
                "Close" : c.close,
                "Volume" : c.vol,
            }
            for c in self.candles[:max_days]
        ]
        data.reverse()
        # timestamp转化成DateTime格式
        index = [pd.to_datetime(timestamp2str(item["Date"])) for item in data] 
        df = pd.DataFrame(data, columns = ["Open", "High", "Low", "Close", "Volume"], index = index)
        df.index.name = 'Date'
        if savefig is not None:
            mpf.plot(df, type = 'candle', volume = volume, mav=mav, figsize=(20, 10), title=self.name, savefig=savefig)
        else:
            mpf.plot(df, type = 'candle', volume = volume, mav=mav, figsize=(20, 10), title=self.name)
        return 
    
    def reduce(self, attr,  num, reduce_fun = "ma", offset = 0):
        """
          对属性attr， offset ~ offset +num这几个candle， 做reduce_fun的操作
          reduce_fun为函数/or string
        """
        fun_map = {
            "ma" : np.mean,
            "min" : np.min,
            "max" : np.max,
            "std" : np.std
        } 
        if reduce_fun in fun_map:
            reduce_fun = fun_map[reduce_fun]
        # 如果取的candles数太高，则强制设置小 
        if num > len(self):
            # logging.error("candle reduce num too large: %s, reset to %s" %(num, len(self)))
            num = len(self)
        assert offset +num  -1 < len(self) , "offset 超出范围 %s>=%s" %(offset + num -1, len(self)) 
        data = [getattr(self[i], attr) for i in range(offset, offset + num)]
        return reduce_fun(data) 
    
    def median_price_estimator(self, days):
        # 预估用户中位数买入价格: 即支撑点之类的
        data = []    # 保存买入价 + 买入量 
        vol_total = 0
        for i in range(days):
            c = self[i]
            price = (c.open + c.close) / 2
            data.append((price, c.vol))
            vol_total += c.vol
        # 加权中位数, 按价格排序
        median_price = 0
        median_vol = vol_total/2
        data.sort(key = lambda x : x[0])
        for item in data:
            median_vol -= item[1]       # 减去量
            if median_vol < 0:          # 中位数
                median_price = item[0]
        return median_price


    def match(self, match_fun, return_date = True):
        """
          统计有多少个candle满足条件, 如match_fun = lambda 
          return_date: 返回第一个不满足的时间
        """
        num = 0
        date = ""  # 最后一个满足条件的日期
        for c in self.candles:
            if match_fun(c):
                num += 1
                date = c.date    # 第一个不满足约束的时间
            else:
                break
        return date if return_date else num

if __name__ == "__main__":
    c = Candle 
    c.high = 123
    c.low = 145
    c.pre_close = 100
    c.close = 105
    print(c.get_rise())