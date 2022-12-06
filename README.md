# 11.28
去掉slot 1   : 8% vs 4%
去掉slot 2/3 : 6% vs 4%
去掉slot 1/2/3: 7% vs 4%
去掉1/2/3/4  :  4%
去掉4        : 10% vs 4%

# 11.29
去掉slot 1/2/3: 6% vs 4%
去掉1/2/3/4  :  2%
去掉4:     %5 vs %4

to-do: 
1. 前复权
   ../training_data/data.bin.20221201_0100
   (1) 0901 + >10%采样2次:  6%
   (2) 0901 5%
   (3) 0901 + 阈值0.02 6% 
   (4) 0901 + 阈值0.05 8%
   (5) 0901 + 阈值0.035 6%
   (6) 0901 + 阈值0.035 + < -0.05采样2次 7%
   (7) 0901 + 阈值0.035 + < -0.05采样2次 9%
   (8) 0901 + 阈值0.035 + < -0.05采样2次 + 删除certainly 5%
   (9) 0901 + 阈值0.035 + < -0.05采样2次 + 删去bias_sum  0%
   (12)0901 + 阈值0.05  + < -0.05采样2次 7%
   (14)0901 + 阈值0.035 + certainly(0.2~1.2) 10%
   (15)0901 + 阈值0.035 + certainly(0.1~1.1) 8%

   ../training_data/data.bin.20221202_1757


   (1) 0901 + 0.035 + < -0.05采样2次 + certainly(0.2)  6%
   (2) 0901 + 0.035  + certainly(0.2) 7%  9%
   (3) 0901 + 0.035  + certainly(0.3) 8%
   (11) 0901 + 0.05  + certainly(0.2) 7%
   (12) 0901 + 30天0.1  + certainly(0.2) 20%  
   (13) 随机采样10%的样本验证集 + + 30天0.1  + certainly(0.2) 25%(数据穿越，因为股票不是完全独立的)
   (14) 随机采样10%的日期 + 30天0.1 certainly(0.2) 25%

  ../log/model_train.log.20221205_1649
  (4) 0901 + 0.035 + certainly(0.2) 6%
  (5) 0901 +0.05 + certainly(0.2) 9%
  (6) 0901 +0.05 + certainly(0.2) + etf 7%
  

# DeepLearningStock
## 代码架构
* update.sh            # 更新项目依赖, 编译Protobuf文件
* run                  # 配置文件
  * run_source.sh     
  * run_feature.sh
  * run_train.sh
  * update.sh          # 依赖 + proto文件更新
  * conf
    * fetch_source.yaml    # 获取source
    * extract_feature.yaml # 抽特征
    * train.yaml           # 模型训练
  * stock.proto        # 中间数据保存
    * message Stock      # 股票数据(k线图、市值等)
    * Message Ins        # 训练数据   
* common               # 通用代码
  * utils.py
  * dag_enging.py      # 运行DAG配置，多线程跑
  * <stock.pb2.proto>    # proto文件编译生成
* source               # 不同地方读取k线图等, 保存为PB类Stock，并存在文件中
  * source.py          # 基类 source, entry: process
  * source_xx.py       # 父类 source
  * r
* feature_extraction   # 根据Stock数据进行特征抽取
  * GlobalData         # 全局数据
  * Context            # 处理过程中每一个Stock的上下文
* model                # 模型训练相关