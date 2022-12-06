from step.step import Step
from common.utils import *
from datetime import datetime
import math
from common.tushare_api import *

class FeatureStep(Step):
    def __init__(self, conf):
        super(FeatureStep, self).__init__(conf)
        self.out_key = conf.get("out_key", "feature_step")    # 一次返回多少context
        pass
    def get_time_feature(self, context):
        """
          时间相关特征
        """
        kline = context.get("source.kline")  
        timestamp = context.get("source.timestamp")
        datetime_obj = datetime.fromtimestamp(timestamp)
        feature = {
            "year" : datetime_obj.year, 
            "month" : datetime_obj.month, 
            "day" : datetime_obj.day,
            "date" : timestamp2str(timestamp, "%Y%m%d"),
            "week" : datetime_obj.weekday()
        }  
        return feature
    def get_recent_rise_feature(self, context):
        """
          最近N天📈📉特征
        """
        kline = context.get("source.kline") 
        feature = {
            "%sd" %(d) : kline.get_rise(d) for d in [1, 3, 7, 30, 180]
        }
        return feature
    def get_vol_related_feature(self, context):
        """
          最近N天成交量变化
        """
        kline = context.get("source.kline")
        feature = {
            # n天内成交额 
            "%sd" %(d) : kline.reduce("vol", d, "ma") for d in [1, 3, 7, 14, 30, 360]
        }
        return feature
    def get_amount_related_feature(self, context):
        # 成交额变化
        kline = context.get("source.kline")   
        feature = {
            # n天内成交额 
            "%sd" %(d) : kline.reduce("amount", d, "ma") for d in [1, 3, 7, 14, 30, 90]
        }
        return feature
    
    def get_all_time_high_feature(self, context):
        # 突破了N天的新高
        kline = context.get("source.kline")   
        feature = {}
        for d in [1, 3, 7, 14]:           
            # 最近d天的最高价格，是过去多少天的最高价格
            high_nd = kline.reduce("high", d, "max")
            feature["%dd" %(d)] = len(kline) -d +1    # 找不到的默认值
            for i in range(d, len(kline)):
                if kline[i].high > high_nd:
                    feature["%dd" %(d)] = i -d +1
                    break 
        return feature
    

    def get_all_time_low_feature(self, context):
        # 突破N天新低
        kline = context.get("source.kline")   
        feature = {}
        for d in [1, 3, 7, 14, 30]:           
            # 最近d天的最低价格，是过去多少天的最低价格
            low_nd = kline.reduce("low", d, "min") 
            feature["%dd" %(d)] = len(kline) -d +1    # 找不到的默认值
            for i in range(d, len(kline)):
                if kline[i].low < low_nd:
                    feature["%dd" %(d)] = i -d +1
                    break 
        return feature

    def get_price_feature(self, context):
        # 价格reduce
        kline = context.get("source.kline")  
        feature = {
            # 最近n天最高价/最低价
            "high_1d" : kline[0].high,
            "low_1d" : kline[0].low,
            "high_3d" : kline.reduce("high", 3, "max"),
            "low_3d" : kline.reduce("low", 3, "min"),
            "high_7d" : kline.reduce("high", 7, "max"),
            "low_7d" : kline.reduce("low", 7, "min"),

            "high_30d" : kline.reduce("high", 30, "max"),
            "low_30d" : kline.reduce("low", 30, "min"),

            "high_60d" : kline.reduce("high", 60, "max"),
            "low_60d" : kline.reduce("low", 60, "min"),

            "high_360d" : kline.reduce("high", 360, "max"),
            "low_360d" : kline.reduce("low", 360, "min"),
            # 均价
            "close" : kline[0].close,                             #  收盘价 
            "close_ma_3d" : kline.reduce("close", 3, "ma"),      # 7日均价
            "close_ma_7d" : kline.reduce("close", 7, "ma"),      # 7日均价
            "close_ma_10d" : kline.reduce("close", 10, "ma"),    # 10日均价
            "close_ma_30d" : kline.reduce("close", 30, "ma"),    # 60日均线
            "close_ma_60d" : kline.reduce("close", 60, "ma"),    # 60日均线
            "close_ma_200d" : kline.reduce("close", 200, "ma"),  # 200日均价
        } 
        # 在200日均线(只计算一个值)上、下运行了多少天
        ma_200d = feature["close_ma_200d"] 
        feature["200d_ma_above_date"] = kline.match(lambda c : c.close > ma_200d, return_date = True) 
        feature["200d_ma_below_date"] = kline.match(lambda c : c.close < ma_200d, return_date = True)
        return feature
    
    def get_median_price(self, context):
        # 获取用户过去n天持仓价格
        kline = context.get("source.kline")  
        feature = {
            "%sd" %(d) : kline.median_price_estimator(d)
                    for d in [14, 30, 60, 180]
        }  
        return feature
    def get_basic_feature(self, context):
        # 基础信息
        kline = context.get("source.kline")  
        if TushareApi.is_etf(kline.ts_code): 
            feature = {
                "pe" : "EMPTY",
                "turnover_rate" :  "EMPTY",
                "turnover_rate_f" : "EMPTY",
                "turnover_rate_f_3d" : "EMPTY",
                "turnover_rate_f_7d" : "EMPTY",
                "turnover_rate_f_30d" : "EMPTY",
                "total_mv" :  "EMPTY"
            }
            return feature
        #例子 {'ts_code': '600519.SH', 'trade_date': '20221122', 'turnover_rate': 0.238, 'volume_ratio': None, 'pe': 36.8753, 'pb': 9.3585}}
        # feature = TushareApi.get_ts_code2basic(kline.ts_code)
        # if math.isnan(feature["pe"]):
        #     feature["pe"] = 10000 
        feature = {
            "pe" : 10000 if kline[0].pe is None or math.isnan(kline[0].pe) else kline[0].pe,    # 市盈率
            "turnover_rate" : kline[0].turnover_rate,      # 换手率(总股本)
            "turnover_rate_f" : kline[0].turnover_rate_f,  # 换手率(流通股本)
            "turnover_rate_f_3d" : kline.reduce("turnover_rate_f", 3, "ma"),  # 换手率(流通股本)
            "turnover_rate_f_7d" : kline.reduce("turnover_rate_f", 7, "ma"),  # 换手率(流通股本)
            "turnover_rate_f_30d" : kline.reduce("turnover_rate_f", 30, "ma"),  # 换手率(流通股本)
            "total_mv" : kline[0].total_mv,  
        }
        # print("%s : %s" %(kline[0].date, feature))
        return feature 

    def get_boll_feature(self, context):
        """
          布林通道相关特征
        """
        kline = context.get("source.kline")  
        n = 20  # 20日线
        m = 2   # 2倍标准差
        ma = kline.reduce("close", n, "ma")
        std = kline.reduce("close", n, 'std')    # 标准差(价差)
        # 布林线
        up  = ma + std*2
        low = ma - std*2
        pos = math.floor((kline[0].close - ma) / std) 
        feature = {
            "up" : up, 
            "low" : low, 
            "mid" : ma,
            "std_rate" : std/kline[0].close,
            "std_rate_200d" : kline.reduce("close", 200, 'std')/kline[0].close,
            # 当前位置: 有5条线，分别是2/1/0/-1/-2倍的标准差, 把pos分成-3, -2, .. ,1, 2
            "pos" : max(min(pos, 2), -3)
        }
        return feature 

    def _execute(self, context):
        """
          原始特征抽取
        """
        feature = {
            "time" : self.get_time_feature(context),
            "recent_rise" : self.get_recent_rise_feature(context),
            "vol" : self.get_vol_related_feature(context),
            "amount" : self.get_amount_related_feature(context),
            "ath" : self.get_all_time_high_feature(context),
            "atl" : self.get_all_time_low_feature(context),
            "price" : self.get_price_feature(context),
            "median_price" : self.get_median_price(context),
            "basic" : self.get_basic_feature(context),# bug, 如PE数据出现穿越
            "boll" : self.get_boll_feature(context)
        } 
        context.set(self.out_key, feature)
        return 
