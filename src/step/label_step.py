from common.utils import *
from step.step import Step
class LabelStep(Step):
    def __init__(self, conf):
        super(LabelStep, self).__init__(conf)
        self.label_confs = conf.get("label_confs", [])
        self.out_key = conf.get("out_key", "label")
        pass

    def next_n_days_high_ratio_method(self, context,  conf, labels):
        """
            接下来的N天内，最高点涨幅是多少
        """
        for d in conf["days"].split(","):
            d = int(d) 
            kline_label = context.get("source.kline_label")
            if len(kline_label) < d:
                continue # 数据不够，不写label 
            open_price = kline_label[-1].pre_close    # 前一天收盘价
            reach_max_price = max([kline.high for kline in kline_label[-d:]])
            # print("开盘价: %s 最高价: %s" %(open_price, reach_max_price))
            if open_price <= 0.01:
                # 加个太低，不写, 避免出现负数
                return 
            labels["next_%sd_high_price" %(d)] = reach_max_price/open_price - 1.0  
        return labels
    
    def execute(self, context):
        labels = {}
        for label_conf in self.label_confs:
            method = label_conf["method"]
            conf = label_conf["conf"]
            # 调用对应的gen_label函数
            getattr(self, method)(context, conf, labels)
        context.set(self.out_key, labels)
        return 
