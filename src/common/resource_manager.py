from common.utils import *
from common.tushare_api import *
# 全局通用
## 上证指数 ##
sh_index = TushareApi.get_kline_by_ts_code("000001.SH", start_date= "", end_date="")
# 上证指数: 时间->candle下标
sh_index_date2idx = {}
for i in range(len(sh_index)):
    c = sh_index[i]
    sh_index_date2idx[c.date] = i 