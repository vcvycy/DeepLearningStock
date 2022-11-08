from source.source_tushare import *

conf = {
      "api_key": "009c49c7abe2f2bd16c823d4d8407f7e7fcbbc1883bf50eaae90ae5f",
      "sample_recent_days":    2,    # 股票采样, 最近N天
      "sample_min_train_days": 1,    # 至少N天数据作为训练数据
      "label_days":            1     # 至少N天的label数据
}

tsrc = TushareSource(conf) 
# print("ctx size: %s" %(tsrc.context_size))
while True:
    ctx = tsrc.get_context()
    if ctx is None:
        break
    print(ctx) 