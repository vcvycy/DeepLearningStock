from step.step import Step
import yaml
import source.feature_hash as feature_hash 
# class FeatureColumn:
class FidExtractionStep(Step):
    def __init__(self, conf):
        super(FidExtractionStep, self).__init__(conf)
        self.in_key = conf.get("in_key", "raw_feature")
        self.out_key = conf.get("out_key", "fids")    # 一次返回多少context
        self.feature_list = yaml.safe_load(open(conf.get("feature_list"), 'r') .read())
        # 
        self.skip_none = self.conf.get("skip_none", True)

        # slot不配置, 自动递增
        self.auto_slot = self.feature_list.get("auto_slot", False)
        self.auto_slot_idx = self.feature_list.get("auto_slot_start", 500)
        self.auto_slot_name_map = {}
        return 

    def get_auto_slot(self, feature_name):
        # 获取slot, 遇到一个新的name就分配新的slot
        if feature_name not in self.auto_slot_name_map:
            self.auto_slot_idx += 1
            self.auto_slot_name_map[feature_name] = self.auto_slot_idx
        assert self.auto_slot_idx < 1024
        return self.auto_slot_name_map[feature_name]
    
    def _execute(self, context): 
        feature = {}  # feature保存 feature_name -> (slot, fid, raw_feature)映射  
        for fc in self.feature_list.get("feature_columns"):
            # 获取参数 
            depends = [d.strip() for d in fc.get("depends").split(",")]
            args = fc.get("args")

            # 获取要执行的函数
            method = getattr(feature_hash, fc.get("method", "BaseMethod"))()
            # 执行函数
            exist_none = False 
            raw_features = []
            for d in depends:
                rf = context.get("%s.%s" %(self.in_key, d))
                if rf is None:
                    exist_none = True 
                raw_features.append(rf)
            if exist_none and self.skip_none:
                continue
            # 特征写到fids
            name = fc.get("name")  
            # 自动分配slot
            slot = fc.get("slot") 
            if slot is None:
                slot = self.get_auto_slot(name)
            else:
                assert slot < self.feature_list.get("auto_slot_start", 500)  # 手工配置的slot不能重复
            try:
                extracted_features, fids = method(raw_features, args, slot)
            except Exception as e:
                print("feature: %s" %(context.get(self.in_key)))
                print("退出程序!Exception:%s %s raw: %s, method: %s" %(e, name, raw_features, method))
                exit(0)
            feature[name] = slot, fids , raw_features, extracted_features
        context.set(self.out_key, feature) 
        return 
