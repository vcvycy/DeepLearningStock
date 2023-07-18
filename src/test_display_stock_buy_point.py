from common.utils import str2timestamp
# from test_parse_log import read, LineItem
from common.tushare_api import TushareApi
import numpy as np
from test_common import read, LineItem, Stats, read_all_item
# l = "INFO 2023-02-02 12:01:25,349 [Top_228665] 黄河旋风 20230201 概率: 0.2886 fid_label_avg: 0.3520 label: None raw_label: 999.000 确定性: 0.702 正确率: 0.39"
# print(LineItem(l))
# exit(0)
def main():
    """
      stock = None, 全部股票一起算，且分天看
      stock != None : 看当前股票
    """
    round = 0
    while True:
        round += 1
        print('-' * 200)
        all_items = read_all_item(end_when = "END")
        if len(all_items) < 10000:
            continue 
        print("round: %s" %(round))
        print("item 数量: %s" %(len(all_items)))
        # if round != 3:
        #     continue
        if args.stocks == "" : 
            stock_names = []
            lastest_date = np.max([item.date for item in all_items])
            for item in all_items:
                if item.date == lastest_date:
                    stock_names.append(item.stock)
            stock_names = stock_names[:5]
            print("没有指定股票，自动取%s top 5的股票： %s" %(lastest_date, stock_names))
        else:
            stock_names = args.stocks.split(",") 
            print("取的股票列表: %s" %(stock_names))
        # exit(0)
        for stock in stock_names:
            date2score = {}
            for item in all_items:
                if stock == item.stock:
                    date2score[str2timestamp(str(item.date), '%Y%m%d') ] = (len(all_items) - item.topk) / len(all_items) -0.5
                    # print(item.date)
            ####
            cur_stock = None 
            for item in TushareApi.get_all_stocks():
                if stock in item["name"]:
                    cur_stock = item
                    break
            print("%s %s" %(cur_stock["name"], cur_stock["ts_code"]))
            get_kline = TushareApi.get_kline_by_ts_code_weekly if args.weekly else TushareApi.get_kline_by_ts_code
            kline = get_kline(cur_stock["ts_code"], start_date= "20100601", end_date="")
            save_path = "image/%s_%s.jpg" %(stock, kline[0].date) if args.stocks is None else None
            kline.draw(date2score = date2score, title = "%s round: %s" %(cur_stock["ts_code"], round), savefig = save_path)
    return 
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--weekly', action='store_true')  # 周线还是日线
    parser.add_argument('-t', '--stocks', type=str, default = "")  # 可以包含多个: 比如宁德时代,西安饮食
    args = parser.parse_args()
    main()