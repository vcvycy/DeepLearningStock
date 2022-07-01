from common.utils import *
from step.step import Step
class LabelStep(Step):
    def __init__(self, conf):
        super(LabelStep, self).__init__(conf)
        self.label_confs = conf.get("label_confs", [])
        pass

    def gen_label_max(self, context,  label_conf):
        """
            接下来的N天内，最高点涨幅是多少
        """
        days = label_conf["days"]
        kline_label = context.get("source.kline_label")
        if len(kline_label) < days:
            # 数据不够，不写label
            return 
        open_price = kline_label[-1].pre_close    # 前一天收盘价
        reach_max_price = max([kline.high for kline in kline_label[-days:]])
        print("开盘价: %s 最高价: %s" %(open_price, reach_max_price))
        if open_price <= 0.1:
            # 加个太低，不写
            return 
        context.set("label.max.%dd" %(days), reach_max_price/open_price - 1.0)
        return 
    
    def execute(self, context):
        for label_conf in self.label_confs:
            label_type = label_conf["type"]
            # 调用对应的gen_label函数
            getattr(self, "gen_label_%s" %label_type)(context, label_conf)
        return 
