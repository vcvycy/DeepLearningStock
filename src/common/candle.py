
import sys
sys.path.append("..")
from common.stock_pb2 import *
import pandas as pd
import mplfinance as mpf 
from common.utils import *
import numpy as np
import logging

class MACD():
    def __init__(self, ema12 = 0, ema26 = 0, dif = 0, dea = 0):
        self.ema12 = ema12
        self.ema26 = ema26
        self.dif = dif
        self.dea = dea
        self.macd = (dif - dea) * 2  # macd柱状值
    def __str__(self):
        return "[macd] ema12=%.2f, ema26=%.2f, dif=%.2f, dea=%.2f" %(self.ema12, self.ema26, self.dif, self.dea)
    
class Candle(): 
    CommonAttr = [
        "date", "open", "high", "low", "close",  "pre_close", "amount", "vol", 
        "turnover_rate", "turnover_rate_f", "pe", 'total_mv',  "time"
    ]
    def __init__(self, date, open, high, low, close, pre_close, amount, vol):
        # super(Candle, self).__init__()
        for attr in Candle.CommonAttr:
            setattr(self, attr, None) 
        self.date = date
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.pre_close = pre_close
        self.amount = amount
        self.vol = vol
        self.macd = None
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

    def get_rise(self, days = 1, offset = 0):
        """
          获取k线图 days天的涨跌幅
          offset ~ offset +days -1
        """
        assert offset + days < len(self), "get_rise超出大小: %s %s %s" %(self.ts_code, days, offset)
        open = self.candles[days + offset].close
        close = self.candles[offset].close
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
        if len(self) == 0:
            return "[Kline %s] k线图为空" %(self.name)
        rsp = "[KLine %s-%s]\n    " %(self.name, self[0].date)
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
            "std" : np.std,
            "sum" : np.sum
        } 
        if reduce_fun in fun_map:
            reduce_fun = fun_map[reduce_fun]
        # 如果取的candles数太高，则强制设置小 
        data = [getattr(self[i], attr) for i in range(offset, min(num, len(self)))]
        return reduce_fun(data) 
    
    def median_price_estimator(self, days):
        # 预估用户中位数买入价格: 即支撑点之类的
        data = []    # 保存买入价 + 买入量 
        vol_total = 0
        for i in range(days):
            if i >= len(self):
                break
            c = self[i]
            # 成交额/成交量=平均成交价格(成交额单位k, 成交量单位手100)
            price = c.amount*10/c.vol #  (c.high + c.low + c.close + c.open) / 4
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
                break
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
    
    def get_macd(self, offset = 0):
        """
          获取macd指标
        """
        c = self[offset]
        # 情况一：已经算过了
        if c.macd is not None:
            return c.macd
        # 情况二：只有一个candle
        if offset == len(self) - 1:  # 最早的candle
            c.macd = MACD()
            c.macd.ema12 = c.macd.ema26 = c.close
            c.macd.dif = 0
            c.macd.dea = 0
            return c.macd
        # 情况三：
        macd_prev = self.get_macd(offset + 1)
        ema12 = macd_prev.ema12 * 11/13 + c.close * 2/13
        ema26 = macd_prev.ema26 * 25/27 + c.close * 2/27
        dif   = ema12 - ema26
        dea   = macd_prev.dea * 8 / 10 + dif * 2/10
        c.macd = MACD(ema12, ema26, dif, dea)
        return c.macd

    def get_ma_k(self, k = 30):
        ma_k = [] 
        k_sum = self.reduce("close", k - 1, reduce_fun = "sum")
        print(self.reduce("close", k))
        for i in range(len(self)):
            j = i + k -1  # k均线: i, i+1, ..., i + k -1
            if j >= len(self):
                break
            k_sum += self[j].close
            ma_k.append(k_sum / k)
            k_sum -= self[i].close 
        return ma_k
    def get_ma_reverse_times(self, k = 30, days = 200):
        """
          最近days天, k均线图的走势反转次数
          反转即: 均线图5个数字，涨涨跌跌 or 跌跌涨涨
        """ 
        ma_k = self.get_ma_k(k)
        # 出现反转
        reverse_idx = []
        for i in range(1, len(ma_k) - 1, 1):
            if (ma_k[i] - ma_k[i-1]) * (ma_k[i] - ma_k[i+1]) > 0 : 
                reverse_idx.append(i)
        # 出现反转
        rsp = 0 
        j = 0
        while j < len(reverse_idx) - 1:
            i1, i2 = reverse_idx[j], reverse_idx[j+1]
            if i2 - i1 >= 5:
                rsp += 1
                print("反转日期: %s" %(self[i1].date))
                j += 1
            else:
                j += 2
        return rsp
if __name__ == "__main__":
    # 在tushare_api.py里测试Kline
    c = Candle 
    c.high = 123
    c.low = 145
    c.pre_close = 100
    c.close = 105
    print(c.get_rise())