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
1. 前复权 ../training_data/data.bin.20221201_0100
   (1) 0901 + >10%采样2次:  6% vs 1%
   (2) 0901 5% vs 1%
   (3) 0901 + 阈值0.02 6% vs 1%
   (4) 0901 + 阈值0.05 8% vs 1%
   (5) 0901 + 阈值0.035 6% vs 1%
   (6) 0901 + 阈值0.035 + < -0.05采样2次 7% vs 1%
   (7) 0901 + 阈值0.05 + < -0.05采样2次 8% vs 1%

   第3次: abs(label) > 0.1采样2次【no bad】
   第4次: abs(label) > 0.1采样2次，abs(label) < 0.01不采样 【bad】
   第5次: label > 0.1 采样2次【no bad】
3. 模型结构: bias_sum / nn / certainly / attention
   第7次: 去掉bias_sum: + 0901 ： 【Top 10 +20%， Top 40 +1%，有很多时间跑输大盘】
4. validedate时间换成0901
   第6次 3% vs 1%

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