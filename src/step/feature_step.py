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
            "date" : timestamp2str(timestamp, "%Y-%m-%d"),
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
            "%sd" %(d) : kline.reduce("vol", d, "ma") for d in [1, 7, 14, 30, 360]
        }
        return feature
    def get_amount_related_feature(self, context):
        # 成交额变化
        kline = context.get("source.kline")   
        feature = {
            # n天内成交额 
            "%sd" %(d) : kline.reduce("amount", d, "ma") for d in [1, 7, 14, 30, 360]
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
            "amount" : self.get_amount_related_feature(context)
        } 
        context.set(self.out_key, feature)
        return 
