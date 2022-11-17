from step.step import Step
from common.utils import *
from datetime import datetime
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
            "%sd" %(d) : kline.reduce("amount", d, "ma") for d in [1, 3, 7, 14, 30, 360]
        }
        return feature
    
    def get_all_time_high_feature(self, context):
        # 突破了N天的新高
        kline = context.get("source.kline")   
        feature = {}
        for d in [1, 3, 7, 14]:           
            # 最近d天的最高价格，是过去多少天的最高价格
            high_nd = kline.reduce("high", d, "max")
            for i in range(d, len(kline)):
                if kline[i].high > high_nd:
                    feature["%dd" %(d)] = i -d +1
                    break 
        return feature
    
    def get_price_feature(self, context):
        # 价格reduce
        kline = context.get("source.kline")  
        feature = {
            # 最近n天最高价/最低价
            "high_1d" : kline.reduce("high", 1, "max"),
            "low_1d" : kline.reduce("low", 1, "min"),
            "low_3d" : kline.reduce("low", 3, "min"),
            "high_3d" : kline.reduce("high", 3, "max"),
            "high_7d" : kline.reduce("high", 7, "max"),
            "low_7d" : kline.reduce("low", 7, "min"),

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
    
    def get_user_hold_price(self, context):
        # 获取用户过去n天持仓价格
        kline = context.get("source.kline")  
        feature = {
            "%sd" %(d) : kline.buy_price_estimator(d)
                    for d in [1, 3, 7, 14, 30]
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
            "price" : self.get_price_feature(context),
            "buy_price" : self.get_user_hold_price(context) 
        } 
        context.set(self.out_key, feature)
        return 
