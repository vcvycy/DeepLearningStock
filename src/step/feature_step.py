from step.step import Step
class FeatureStep(Step):
    def __init__(self, conf):
        super(FeatureStep, self).__init__(conf)
        self.out_key = conf.get("out_key", "feature_step")    # 一次返回多少context
        pass

    def execute(self, context):
        feature = {}
        kline = context.get("source.kline")
        print(kline[0])
        feature["rise_1d"] = kline.get_rise(1)
        feature["rise_3d"] = kline.get_rise(3)
        feature["rise_7d"] = kline.get_rise(7)
        context.set(self.out_key, feature)
        return 
