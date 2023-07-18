from common.utils import *
from step.step import Step
import numpy
class LabelStep(Step):
    def __init__(self, conf):
        super(LabelStep, self).__init__(conf)
        self.label_confs = conf.get("label_confs", [])
        self.out_key = conf.get("out_key", "label")
        pass

    def next_n_days_method(self, context,  conf, labels):
        """
            接下来的N天内, 最高/最低/收盘价格
        """
        # 14～200天前的最高点，最低点. 然后在区间内计算百分比
        high = max(context.get("raw_feature.price.high_90d_200d"),
                    context.get("raw_feature.price.high_14d_90d"))
        low = max(context.get("raw_feature.price.low_90d_200d"),
                    context.get("raw_feature.price.low_14d_90d"))
        assert high - low > 0, "%s <= %s" %(high, low)

        kline_label = context.get("source.kline_label")
        key = conf.get("key") 
        for d in conf["days"].split(","):
            d = int(d) 
            if len(kline_label) < d:
                continue # 数据不够，不写label 
            open_price = kline_label[-1].open    # 第二天开盘价作为open price
            if open_price <= 0.01:
                # 加个太低，不写, 避免出现负数
                return 
            # 最高价格
            max_price = max([kline.high for kline in kline_label[-d:]]) 
            labels["next_%sd_max_price" %(d)] = float_trun(max_price/open_price - 1.0)  
            # 最低价格
            min_price = min([kline.low for kline in kline_label[-d:]]) 
            labels["next_%sd_min_price" %(d)] = float_trun(min_price/open_price - 1.0)
            # 收盘价格
            close_price = kline_label[-d].close
            labels["next_%sd_close_price" %(d)] = float_trun(close_price/open_price - 1.0)
            # 平均收盘价
            mean_price = numpy.mean([kline.close for kline in kline_label[-d:]]) 
            labels["next_%sd_mean_price" %(d)] =  float_trun(mean_price/open_price -1.0)
            # 归一化(即将最低点 -> 最高点强制设置为涨100%)后的涨幅
            labels["next_%sd_norm_price" %(d)] = float_trun((close_price - open_price) / (high - low))
        
        if len(kline_label) >=14:
            mean_7d_14d = numpy.mean([kline.close for kline in kline_label[-14:-7]]) 
            # print("%s %s" %(kline_label[-1].date, [kline.close for kline in kline_label[-14:-7]]))
            labels["next_7d_14d_mean_price"] = float_trun(mean_7d_14d/open_price -1.0)
        if len(kline_label) >=7:
            mean_3d_7d = numpy.mean([kline.close for kline in kline_label[-7:-3]]) 
            # print("%s %s" %(kline_label[-1].date, [kline.close for kline in kline_label[-14:-7]]))
            labels["next_3d_7d_mean_price"] = float_trun(mean_3d_7d/open_price -1.0)
        return labels

    def _execute(self, context):
        labels = {}
        for label_conf in self.label_confs:
            method = label_conf["method"]
            conf = label_conf["conf"]
            # 调用对应的gen_label函数
            getattr(self, method)(context, conf, labels)
        context.set(self.out_key, labels)
        return 
