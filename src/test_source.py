from source.source_tushare import *

conf = {
      "api_key": "009c49c7abe2f2bd16c823d4d8407f7e7fcbbc1883bf50eaae90ae5f",
      "sample_recent_days":    2,    # 股票采样, 最近N天
      "sample_min_train_days": 1,    # 至少N天数据作为训练数据
      "label_days":            1     # 至少N天的label数据
}

# tsrc = TushareSource(conf)
# import time
# time.sleep(1)
# print("ctx size: %s" %(tsrc.context_size))
# while True:
#     ctx = tsrc.get_context()
#     if ctx is None:
#         break
#     print(ctx)

client = TushareApi.init_client(conf["api_key"])
print(TushareApi.get_kline_by_ts_code(client, "002241.SZ")[-1])
print(TushareApi.get_kline_by_ts_code(client, "000001.SZ")[-1])
# import ipdb;ipdb.set_trace()
