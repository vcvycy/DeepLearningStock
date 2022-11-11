
import sys
sys.path.append("..")
from common.stock_pb2 import *
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
    def __init__(self, name="unknown", candles = None):
        self.name = name
        self.candles = [] if candles is None else candles
    
    def add(self, candle):
        self.candles.append(candle)
        return 
    
    def get_rise(self, days = 1):
        """
          获取k线图 days天的涨跌幅
        """
        if days >= len(self.candles):
            days = len(self.candles) - 1
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
        if len(self.candles) > 10:
            rsp += str(self.candles[:2]) + "..." + str(self.candles[-2:])
        else: 
            rsp += str(self.candles)
        return rsp
    
if __name__ == "__main__":
    c = Candle 
    c.high = 123
    c.low = 145
    c.pre_close = 100
    c.close = 105
    print(c.get_rise())