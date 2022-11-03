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
            "rise_1d" : kline.get_rise(1),
            "rise_3d" : kline.get_rise(3),
            "rise_7d" : kline.get_rise(7)
        }
        return feature
    def execute(self, context):
        """
          原始特征抽取
        """
        feature = {
            "time" : self.get_time_feature(context),
            "recent_rise" : self.get_recent_rise_feature(context)
        } 
        context.set(self.out_key, feature)
        return 
