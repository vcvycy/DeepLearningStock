import re
tot = {}
corr = {}
raw_label_sum = {}
rank = {}
outputs = {}
thresholds = set([5 * 2**i for i in range(20)])
# print(thresholds)
# exit(0)

def get_certainly_val(line):
    l2 = line.split("确定性: ")
    if len(l2) == 1:
        return 1
    else:
        return float(l2[1].split(" ")[0]) 

def add_stats(date, label, raw_label, topk):
    global tot 
    global corr 
    global raw_label_sum
    global thresholds
    global rank
    if date not in tot:
        tot[date] = 0
        corr[date] = 0
        rank[date] = 0
        outputs[date] = ""
        raw_label_sum[date] = 0
    tot[date] += 1
    corr[date] += label
    rank[date] +=  topk
    raw_label_sum[date] += raw_label
    if tot[date] in thresholds: 
        outputs[date] += "总数: %5d, 真实数量: %5d 正确率: %.2f%% 原始label均值: %.2f 平均排名: %.1f\n"  %(tot[date], 
            corr[date], 100*corr[date]/tot[date], raw_label_sum[date] / tot[date],  rank[date]/tot[date])
    return 

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

def main(stock = None, show_date = False, certainly_threshold = 0):
    """
      stock = None, 全部股票一起算，且分天看
      stock != None : 看当前股票
    """
    global tot 
    global corr 
    global raw_label_sum
    global rank
    global outputs
    round = 0
    while True:
        print('-' * 200)
        tot = {}
        corr = {}
        raw_label_sum = {}
        rank = {}
        outputs = {}
        round += 1
        certain_filter_cnt = 0
        while True: 
            line = read()
            if line == "END":
                break
            if stock is not None:
                if stock not in line:
                    continue
                print(line)
            if "Top_" not in line:
                continue
            topk = int(re.findall("Top_\d+", line)[0][4:]) 
            try:
                date = re.findall("202[0-5]\d{4,4}",line )[0]
                label = int(line.split(" label: ")[1][0])
                raw_label = float(line.split("raw_label: ")[1].split(" ")[0])
            except:
                continue
            assert raw_label < 5
            if get_certainly_val(line) < certainly_threshold:
                certain_filter_cnt += 1
                continue
            if show_date:
                add_stats(date, label, raw_label, topk) 
            add_stats("ALL_TIME", label, raw_label, topk)
        dates = list(tot)
        dates.sort(key = lambda x : x)
        for date in dates: 
            print(("第%s次运行结果-%s" %(round,date)).center(100, "=")) 
            print(outputs[date])
            print( "总数: %5d, 正例数量: %5d 正确率: %.2f%% 原始label均值: %.2f 平均排名: %.1f\n"  %(tot[date], 
                    corr[date], 100*corr[date]/tot[date], raw_label_sum[date] / tot[date],  rank[date]/tot[date]))
        print("注: 过滤确定性低的股票： %s个" %(certain_filter_cnt))
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', type=str, default=None) 
    parser.add_argument('-d', '--date', action='store_true')
    parser.add_argument('-c', '--certainly-threshold', type=float, default = 0)
    args = parser.parse_args()
    main(args.name, show_date = args.date, certainly_threshold = args.certainly_threshold)