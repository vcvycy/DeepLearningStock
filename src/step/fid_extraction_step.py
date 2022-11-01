from step.step import Step
import yaml
import source.feature_methods as feature_methods 
class FidExtractionStep(Step):
    def __init__(self, conf):
        super(FidExtractionStep, self).__init__(conf)
        self.in_key = conf.get("in_key", "raw_feature")
        self.out_key = conf.get("out_key", "fids")    # 一次返回多少context
        self.feature_list = yaml.safe_load(open(conf.get("feature_list"), 'r') .read())
        return 


    def get_fids(self, context):
        fids = []
        return []
    def execute(self, context):
        feature = {
            "fids" : []
        }  
        for fc in self.feature_list.get("feature_columns"):
            # 获取参数 
            depends = fc.get("depends").split(",")
            args = fc.get("args")
            slot = fc.get("slot")
            # 获取要执行的函数
            method = getattr(feature_methods, fc.get("method"))()
            # 执行函数
            raw_features = [context.get("%s.%s" %(self.in_key, d)) for d in depends]
            # 特征写到fids
            feature["fids"].extend(method(raw_features, args, slot))

        context.set(self.out_key, feature)
        return 
