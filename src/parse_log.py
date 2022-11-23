tot = 0
corr = 0
threshold = 10
while True:
    date = "20221104"
    try:
        item = input("")
    except:
        break
    try:    
        if date not in item:
            continue
        label = item.split("真实label: ")[1]
        label = int(label[0])
        tot += 1
        if label == 1:
            corr += 1
        if tot == threshold:
            print("总数: %5d, 真实数量: %5d 正确率: %.2f%%"  %(tot, corr, 100*corr/tot))
            threshold *= 2
    except Exception as e:
        # print("Except: %s" %(e)) 
        pass
if tot> 0:
    print("总数: %5d, 真实数量: %5d 正确率: %.2f%%"  %(tot, corr, 100*corr/tot))