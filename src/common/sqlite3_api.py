import os
import sys 
import sqlite3
import json
current_dir = os.path.dirname(os.path.abspath(__file__)) 
parent_dir = os.path.dirname(current_dir) 
sys.path.append(parent_dir)
from common.stock_pb2 import Instance, FeatureColumn
from common.utils import enum_instance
from tqdm import tqdm
"""
  数据库名: DATABASE_NAME
  数据表: 
     1. 创建 stock 表
        CREATE TABLE IF NOT EXISTS Stock (
                name TEXT,
                ts_code TEXT,
                date TEXT,
                total_mv INTEGER,
                label JSON,    -- JSON格式 {"3day": "xx"}
                feature JSON,  -- JSON格式 [{"slot": 1, "fid": 1234}]
                PRIMARY KEY (ts_code, date)
        );
    2. 建索引:
       CREATE INDEX my_index ON Stock (name, ts_code, date);

""" 
DATABASE_NAME = "stock.sqlite3.db"
def write_instances(instances):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor() 
    # 插入多条数据到 Stock 表格
    insert_query = """
        INSERT OR REPLACE INTO Stock (name, ts_code, date, total_mv, label, feature)
        VALUES (?, ?, ?, ?, ?, ?)
        """
    data_list = []
    for ins in instances:
        feature = [{
            "name" : f.name,
            "slot" : f.slot,
            "fids" : list(f.fids),
            # 下面2个可以不写
            "raw_feature" : list(f.raw_feature),
            "extracted_features" : list(f.extracted_features)
        } for f in ins.feature] 
        
        item = (
            ins.name,
            ins.ts_code, 
            ins.date,
            ins.total_mv, 
            json.dumps({k : ins.label[k] for k in ins.label}),
            json.dumps(feature)
        )
        data_list.append(item)  
    cursor.executemany(insert_query, data_list)
    conn.commit()
    return 
def read_instances(batch_size = 1000):
    def to_ins(row):
        ins = Instance() 
        ins.name = row['name']
        ins.ts_code = row['ts_code']
        ins.date = row['date']
        ins.total_mv = row['total_mv']  
        label = json.loads(row['label'])
        for key in label:
            val = label[key] 
            ins.label[key] = val
        feature = json.loads(row['feature']) 
        for item in feature:
            fc = FeatureColumn()
            fc.name = item['name']
            fc.slot = item['slot']
            fc.fids.extend(item['fids'])
            fc.raw_feature.extend(item['raw_feature'])
            fc.extracted_features.extend(item['extracted_features'])
            ins.feature.extend([fc])
        return ins
    # 连接到 SQLite3 数据库
    conn = sqlite3.connect(DATABASE_NAME) 
    cursor = conn.cursor() 
    cursor.execute("SELECT COUNT(*) FROM Stock")
    table_count = cursor.fetchall()[0][0]
    bar = tqdm(total = table_count)
    cursor.execute('SELECT * FROM Stock') 
    columns = [description[0] for description in cursor.description]
    items = []
    while True:
        # 读取指定大小的数据行
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        for row in rows:
            bar.update(1)
            row_dict = dict(zip(columns, row))
            items.append(row_dict)
            input(row_dict)
            # ins = to_ins(row_dict)
            # # 进行数据处理操作
            # yield ins
            yield row_dict

    # 关闭游标和数据库连接
    cursor.close()
    conn.close()
    return 

if __name__ == "__main__":
    # 需要在上一级目录执行
    # for ins in enum_instance('../training_data/data.daily.20230907_1801'): 
    #     write_instances([ins])
        # break
    for ins in read_instances():
        # print(ins)
        pass