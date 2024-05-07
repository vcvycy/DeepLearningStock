#coding=utf8
from common.tushare_api import * 
print("输入股票名字 or ts_code:")
client = TushareApi.init_client()
all_stocks = TushareApi.get_all_stocks(client)
while True:
    item = input("")
    for i in range(all_stocks.shape[0]):
        name = all_stocks.at[i, "name"]
        ts_code = all_stocks.at[i, "ts_code"] 
        if name in item or ts_code in item:
            print(item)
            kline = TushareApi.get_kline_by_ts_code(client, all_stocks.at[i, "ts_code"])
            kline.name = name
            kline.draw(max_days = 30)