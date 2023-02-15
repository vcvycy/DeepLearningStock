from step.step import Step
from common.utils import *
from datetime import datetime
import math
from common.tushare_api import *
from common import resource_manager as RM

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
            "%sd" %(d) : kline.get_rise(d) for d in [1, 3, 7, 14, 30, 180]
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
        """
          最近N天成交额变化
        """
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
            high_nd = kline.reduce("close", d, "max") # 收盘价
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
            "high_180d" : kline.reduce("high", 180, "max"),

            "high_7d_14d" : kline.reduce("high", 14, "max", offset = 7),
            "low_7d_14d" : kline.reduce("low", 14, "min", offset = 7),

            "high_14d_90d" : kline.reduce("high", 90, "max", offset = 14),
            "low_14d_90d" : kline.reduce("low", 90, "min", offset = 14),

            "high_90d_200d" : kline.reduce("high", 200, "max", offset = 90),
            "low_90d_200d" : kline.reduce("low", 200, "min", offset = 90),
            # 均价
            "open" : kline[0].open,
            "pre_close" : kline[0].pre_close,
            "close" : kline[0].close,                             #  收盘价 
            "close_ma_3d" : kline.reduce("close", 3, "ma"),      # 3日均价
            "close_ma_5d" : kline.reduce("close", 5, "ma"),      # 5日均价
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
                    for d in [14, 30, 90]#, 180]
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
            "std_rate_14d" : kline.reduce("close", 14, 'std')/kline[0].close,
            "std_rate_60d" : kline.reduce("close", 60, 'std')/kline[0].close,
            "std_rate_200d" : kline.reduce("close", 200, 'std')/kline[0].close,
            # 当前位置: 有7条线，分别是3/2/1/0/-1/-2/-3倍的标准差, 把pos分成-4, -3, .. ,1, 2, 3
            "pos" : max(min(pos, 3), -4)
        }
        return feature 
    
    def get_macd_feature(self, context):
        """
          macd相关特征
        """
        kline = context.get("source.kline")  
        macd = kline.get_macd()
        # 上一次交叉的时间: 如果绿变红，则为正数；否则为负数
        num = 0
        while num < 50:
            num += 1
            macd_prev = kline.get_macd(num)
            if (macd.dif -macd.dea) * (macd_prev.dif -macd_prev.dea) < 0:
                break
        if macd.dif - macd.dea < 0:
            num = -num
        feature = {
            "dif_cmp_close" : macd.dif / kline[0].close,
            "dea_cmp_close" : macd.dea / kline[0].close,
            "macd" : macd.macd,
            "pos_num" : num
        }
        return feature
    
    def get_dense_last_n_day(self, context):
        """
          dense特征
        """
        kline = context.get("source.kline") 
        assert len(kline) >= 30, "dense特征失败, len < 30"
        close = kline[0].close
        feature = {
            "last_30d_close" : [(kline[i].close -close)/close for i in range(30)]
        } 
        return feature

    def get_ma_reverse(self, context):
        """
          统计 k 日均线图，最近n天出现几次趋势反转
        """
        kline = context.get("source.kline") 
        ma_k = 10
        candle_idxs = kline.get_ma_reverse_times(k = ma_k) 
        # for c, is_rise in candle_idxs:
        #     print("%s %s" %(kline[c].date, "up" if is_rise else "down"))
        feature = {}
        for days in [10, 30, 90, 180]:
            cnt = 0
            for idx, is_rise in candle_idxs:
                if idx < days:
                    cnt += 1
                # else:
                #     break
            feature["ma_%d_%dd" %(ma_k, days)] = cnt  
        return feature

    def get_sh_index_feature(self, context):
        """
          上证指数
        """
        kline = context.get("source.kline") 
        # 指数最近1/3/7/14/30天涨跌
        feature = {}
        # 保证指数日期和当前采样的k线图一致
        sh_index_offset = RM.sh_index_date2idx[kline[0].date]
        for d in [1,3,7,14, 30]:
            # 上证指数最近d天涨跌
            feature["rise_%dd" %(d)] = RM.sh_index.get_rise(d, sh_index_offset) 
            # 最近d天是否跑赢上证指数
            feature["surpass_%dd" %(d)] = kline.get_rise(d) - RM.sh_index.get_rise(d, sh_index_offset)
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
            "boll" : self.get_boll_feature(context),
            "macd" : self.get_macd_feature(context),
            # dense 特征
            "dense" : self.get_dense_last_n_day(context),
            # 上证指数
            "sh_index" : self.get_sh_index_feature(context),
            # 均线反转次数
            # "trend_reversal" : self.get_ma_reverse(context)
        } 
        context.set(self.out_key, feature)
        return 
