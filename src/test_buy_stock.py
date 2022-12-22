import re
from common.tushare_api import *
class Acount:
    def __init__(self):
        self.all_stocks = TushareApi.get_all_stocks()
        self.ts2kline = {}
        self.money = 1
        self.hold = {}
        return 
    def get_kline(self, name):
        ts_code = ""
        for item in self.all_stocks:
            if name in item["name"] or name in item["ts_code"]:
                ts_code = item["ts_code"]
        if ts_code not in self.ts2kline:
            self.ts2kline[ts_code] = TushareApi.get_kline_by_ts_code(ts_code, start_date= "20220926", end_date="")
        return self.ts2kline[ts_code]
    def buy(self, name, date):
        if self.money < 0.1:
            print("买不起")
            return 
        kline = self.get_kline(name) 
        for c in kline:
            if c.date == date:
                # print("buy %s at %s, price: %s" %(name, date, c.close))
                self.money -= 0.1
                self.hold[name] = {
                    "vol" : 0.1,
                    "price" : c.close,
                    "buy_date" : date
                }
        return 
    def sell(self, name, date):
        kline = self.get_kline(name)
        for c in kline:
            if c.date == date:
                k = self.hold[name]["vol"]
                k *= c.close/ self.hold[name]["price"]
                self.money += k 
                print("buy %s at %s , price: %s sell at: %s %s"  %(name, self.hold[name]["buy_date"],
                             self.hold[name]["price"], date, c.close))
        return 

if __name__ == "__main__":
    acount = Acount()
    acount.buy("长城汽车", "20221114")
    acount.sell("长城汽车", "20221129")
    print("最终盈利: %s" %(acount.money))
    exit(0)
def read():
    try:
        line = input("")
        if "END" in line:  # 表示分隔符
            return "END"
        else:
            return line
    except Exception as e:
        print("Exception: %s" %(e))
        exit(0)

def main(show_date = False):
    """
      stock = None, 全部股票一起算，且分天看
      stock != None : 看当前股票
    """ 
    round = 0
    while True:
        print('-' * 200) 
        while True: 
            line = read()
            if line == "END":
                break 
            if "Top_" not in line:
                continue
            topk = int(re.findall("Top_\d+", line)[0][4:]) 
            date = re.findall("202[0-5]\d{4,4}",line )[0] 
            raw_label = float(line.split("raw_label: ")[1].split(" ")[0])

            if raw_label > 100:
                continue 
            if topk < 100:
                print(line)
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--date', action='store_true') 
    args = parser.parse_args()
    main(show_date = args.date)