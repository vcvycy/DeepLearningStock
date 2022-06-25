# DeepLearningStock
## 代码架构
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
    * class Stock      # 股票数据(k线图、市值等)
    * class Ins        # 训练数据   
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