import sys
sys.path.append("..")
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

#####
ts_code2company = {}
class Company:
    def __init__(self, item):
        self.ts_code = item['ts_code']
        self.province = item['province']        # 省份
        self.employees = item['employees']      # 员工数  (p5:196, p95: 17000)
        self.reg_capital = item['reg_capital']  # 注册资本 (p5: 7660, p95: 45万)
        if self.employees is None or math.isnan(self.employees):
            self.employees = "EMPTY"
        self.item = item 
    def __str__(self):
        return str(self.item)

for idx, item in TushareApi.get_stock_company().iterrows(): 
    ts_code = item['ts_code'] 
    ts_code2company[ts_code] = Company(item)

#################

if __name__ == "__main__":
    import numpy as np
    import math

    keys = ['employees', 'reg_capital']
    items = [ts_code2company[ts_code] for ts_code in ts_code2company]
    for k in keys:
        data = [getattr(item, k) for item in items if getattr(item, k) != "EMPTY"]
        print(data[:10])
        print(k, np.mean(data), np.percentile(data, 25))
        for pk in [5, 10, 25, 50, 75, 90, 95]:
            print(f"p{pk} = %s" %(np.percentile(data, pk)))