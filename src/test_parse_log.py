import re
tot = {}
corr = {}
raw_label_sum = {}
rank = {}
outputs = {}
thresholds = set([5 * 2**i for i in range(20)])
# print(thresholds)
# exit(0)
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
        if "sum(bias-label)" in line:  # 表示分隔符
            return "END"
        else:
            return line
    except:
        print("文件结束")
        exit(0)

def main():
    global tot 
    global corr 
    global raw_label_sum
    global rank
    global outputs
    round = 0
    while True:
        tot = {}
        corr = {}
        raw_label_sum = {}
        rank = {}
        outputs = {}
        round += 1
        while True: 
            line = read()
            if line == "END":
                break
            
            if "Top_" not in line:
                continue
            topk = int(re.findall("Top_\d+", line)[0][4:]) 
            date = re.findall("2022[0-9]{4,4}",line )[0]
            try:
                label = int(line.split(" label: ")[1][0])
                raw_label = float(line.split("raw_label: ")[1].split(" ")[0])
            except:
                continue
            assert raw_label < 5
            add_stats(date, label, raw_label, topk) 
            add_stats("ALL_TIME", label, raw_label, topk)
        dates = list(tot)
        print(dates)
        dates.sort(key = lambda x : x)
        for date in dates: 
            print(("第%s次运行结果-%s" %(round,date)).center(100, "=")) 
            print(outputs[date])
            print( "总数: %5d, 真实数量: %5d 正确率: %.2f%% 原始label均值: %.2f 平均排名: %.1f\n"  %(tot[date], 
                    corr[date], 100*corr[date]/tot[date], raw_label_sum[date] / tot[date],  rank[date]/tot[date]))
if __name__ == "__main__":
    main()