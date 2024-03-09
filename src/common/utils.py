#coding=utf8
import time
import struct
import psutil
import re
import json
from google.protobuf.internal import api_implementation
assert api_implementation.Type() != 'python', "%s 非常慢!!" %(api_implementation.Type())

def get_memory_usage():
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_usage = memory_info.rss  # 获取实际物理内存占用，单位为字节
    memory_usage_mb = memory_usage / (1024 * 1024)  # 转换为MB 
    print(f"当前内存占用：{memory_usage_mb} MB")
# 浮点数保留k位小数
def float_trun(f, k = 3):
    try:
        f = float(f)
        return 1.0 * int(f * 10 ** k) / (10 ** k) 
    except:
        return f

def pretty_json(data, prefix = ""):
    def show(data, prefix= ""):
        s = ""
        for k in data:
            v = data[k]
            if isinstance(v, dict):
                s += "%s %s:\n%s" %(prefix, k, show(v, prefix+"  "))
            else: 
                val = str(v).replace("\n", " ")
                if len(val) > 300:
                    val = val[:300] + "...(共%s字符)" %(len(val))
                s += "%s %s: %s\n" %(prefix, k, val)
        return s
    data = show(data, prefix)
    return data

def write_file_with_size(f, binary):
    """
      二进制数据保存到文件中, 字节数8位存在前8
    """
    size = len(binary) 
    f.write(struct.pack('Q', size))
    f.write(binary)
    return 

def read_file_with_size(f, PBClass = None):
    data_size_bin = f.read(8)
    if len(data_size_bin) < 8:
        return 0, None
    data_size = struct.unpack('Q', data_size_bin)[0]
    assert data_size < 2**20
    data = f.read(data_size)
    if PBClass is not None:
        obj = PBClass()
        obj.ParseFromString(data)
        data = obj
    return data_size, data

def enum_instance(path, max_ins = 1e10):
    """
      path : 训练文件，可以单个，或者多个
      max_ins: 最多读取多少样本
    """
    from common.stock_pb2 import Instance
    from tqdm import tqdm
    if not isinstance(path, list):
        path = [path]
    bar = tqdm(total = 1000000)
    hash_set = set()
    for p in path:
        f = open(p, "rb")
        while True:
            size, data = read_file_with_size(f, Instance)
            if size == 0 or max_ins <= 0:
                break
            hash_key = data.ts_code + data.date
            if hash_key in hash_set:
                continue
            hash_set.add(hash_key)
            max_ins -= 1
            # if max_ins %10000 == 0:
            #     get_memory_usage()
            bar.update(1)
            yield data
    return 


def str2timestamp(timestr, format = "%Y-%m-%d %H:%M:%S"): 
    timeArray = time.strptime(timestr, format) 
    return int(time.mktime(timeArray))

def timestamp2str(ts = int(time.time()), format = "%Y-%m-%d %H:%M:%S"):
    return time.strftime(format,time.localtime(int(ts)))

def coloring(string, pattern = ".*", color = "red"):
    """
       输出str, 其中pattern中的匹配的子串用颜色替换
    """
    def __coloring(s):
        if color == "green" : 
            return "\033[1;32m%s\033[0m" %(s.group())  # 绿色字体
        elif color == "red" : 
            return "\033[1;31m%s\033[0m" %(s.group())  # 绿色字体
        elif color == "yellow":
            return "\033[1;33m%s\033[0m" %(s.group())  # 黄色字体
        return s  
    return re.sub(pattern, __coloring, string) 

class NumpyEncoder(json.JSONEncoder):
    """ Custom encoder for numpy data types """
    def default(self, obj):
        import numpy as np
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NumpyEncoder, self).default(obj)
 
def mprint(data, col_names = None, title = ""):
    """
      data为数组，数组元素为 list/tuple/map;
      如果是map类型，转为list，然后送入__mprint()
      map 类型经常导致列顺序乱掉，自定义列名顺序
      用法:
        mprint([1,2,3],[5,6,7])
        mprint([{"name": "cjf", "age" : 11}, {"name": "cjj", "age" : 22}], col_names=["age", "name"])
    """
    def __mprint(mat, title = "", max_col_size = 150):
        """
        二维数组(tuple)输出,           【如果一行输出太长，那么限制每一列的大小不超过19】
        max_col_size: 每一列最长多少;
        MPRINT_MAX_COL_SIZE: 所有列加起来最长多少
        
        output_post_fun : 对每一个数据做处理
        """
        def get_width(val):
            from wcwidth import wcwidth
            width = 0
            for c in str(val):
                width += wcwidth(c)
            return width
        def to_str(s): 
            if type(s) == type(b""):
                s = s.decode("utf-8")
            if isinstance(s, float):
                s = "%.5f" %(s)
            return str(s)
        def __expand_col_size_excceed_limit(mat, max_col_size):
            """
            某一列长度太长，分成多行显示
            """
            def split_as_list_by_col_size(l):
                # 按照长度最多19拆分成list 
                List = [] 
                for s in l:
                    val = "%s" %s 
                    while len(val) > 0:
                        List.append(val[:max_col_size])
                        val = val[max_col_size:]
                return List
            mat2 = []
            for row in mat:
                row = list(row)  # 复制一个list 防止tuple的情况无法assiment && 防止mat中的值被改动
                # 转为string 
                for cid in range(len(row)):
                    # 每一列拆分成多行显示
                    if isinstance(row[cid], dict):
                        row[cid] = ["[%s] %s" %(k, to_str(row[cid][k])) for k in row[cid]]
                    elif isinstance(row[cid], list):
                        pass
                    else:
                        # 非list/map类型,转换成string类型, 然后每一列最多19个字符 
                        row[cid] = to_str(row[cid]).split("\n")  
                    row[cid] = split_as_list_by_col_size(row[cid])    
                # 每一行拆分成多行
                split_rows = 0
                for col in row:
                    split_rows = max(split_rows, len(col))
                
                for i in range(split_rows):
                    new_row = []
                    for col in row:
                        new_row.append(str(col[i]) if len(col) > i else "")
                    mat2.append(new_row) 
            return mat2
        MPRINT_MAX_COL_SIZE = 200 
        if len(mat) == 0 or len(mat[0]) == 0:
            return 
        tmp_mat = mat[:]
        # mat = __expand_col_size_excceed_limit(mat, max_col_size)
        col_size = [0 for _ in mat[0]]   # 每一列占的width
        for row in mat: 
            for cid in range(len(row)):
                row[cid] = to_str(row[cid])   # 全部转为string类型
                col_size[cid] = max(col_size[cid], get_width(row[cid]))
        sum = 4
        for c in col_size:
            sum += c + 2  # 2表示前后都有个空格
        # print("sum=%s max_col_size: %s" %(sum, max_col_size))
        if sum > MPRINT_MAX_COL_SIZE and max_col_size > 19: # 19使得GID一行放得下
            __mprint(tmp_mat, title = title, max_col_size = max_col_size - 1)
            return 
        # 上边框
        tlen = get_width(title)  # title长度
        boder_horizon = "%s%s%s" % ("-" * ((sum - tlen - 2) >>1), 
            title, "-" * ((sum - tlen -1)>>1))
        print_data = []
        print_data.append(boder_horizon)

        for item in mat:
            # str_arr = [x.decode("utf8") if type(x) == type(b"") else x for x in item]
            str_out = "|"
            for i, width in enumerate(col_size):
                str_out += " " + str(item[i]) + " " * (width - get_width(item[i])) + " "
            str_out += "|"
            # str_out = format %(tuple(str_arr))
            str_out = coloring(str_out, pattern = "\[[^ ]+\]", color="yellow")
            str_out = coloring(str_out, pattern = "#[a-zA-Z_]+|preds", color="red")
            str_out = coloring(str_out, pattern = "![a-zA-Z_]+|stats_tag", color="green")
            print_data.append(str_out)
        #下边框
        print_data.append('-'*sum)
        print("\n".join(print_data))
        return 
    mat = data
    if type(data) == type({}):
        mat=[["KEY", "VALUE"]] + [[k, data[k]] for k in data]
    elif len(data) > 0 and type(data[0]) == type({}):
        if col_names == None:
            col_names = list(data[0])
        mat = [col_names, ["" for _ in col_names]]
        for item in data:
            row = []
            for key in col_names:
                row.append(item[key])
            mat.append(row) 
    __mprint(mat, title = title)
    return 


def print_json(item, dep= 0):
    import numpy as np
    def print_val(val):
        val = str(val).split("\n")
        val = [l[:200] for l in val]
        if len(val) == 1:
            print(val[0])
        else:
            print("")
            for l in val:
                print(f"{'    '* dep}    |{l}")
        return 
    is_list = lambda x : isinstance(x, list) or isinstance(x, np.ndarray)
    if isinstance(item, dict):
        for key in item:
            val = item[key]
            print(f"{'    '*dep}- {key}", end=" : ") 
            if isinstance(val, dict) or is_list(val):
                print("")
                print_json(item[key], dep+1)
            else:
                print_val(val)
    elif is_list(item):
        for i in range(len(item)):
            print(f"{'    '*dep}- [{i}]", end=" : ")
            if isinstance(item[i], dict):
                print("")
                print_json(item[i], dep + 1)
            else:
                print_val(item[i])
    return 

def group_by_key(all_items, key):
    key2items = {}
    for item in all_items:
        if isinstance(key, str):
            k = item[key]
        else:
            k = key(item)
        if k not in key2items:
            key2items[k] = []
        key2items[k].append(item)
    return key2items
    
def read_parquet_or_jsonl(path_glob):
    """ 读取 Parquet 文件, 默认为jsonl (支持glob匹配)
    """
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    def read_one(path):
        path = process_path(path)   # hdfs支持
        if path.split(".")[-1] == 'parquet':
            df = pd.read_parquet(path)
            return [row.to_dict() for _, row in df.iterrows()]
        elif path[-4:] == ".csv":
            import csv
            # with open(path, 'r') as file:  # 这个会出现\ufeff
            with open(path, 'rU', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file)
                return [row for row in csv_reader]
        else:
            return [json.loads(l) for l in open(path, "r").readlines() if l.strip() != ""]
    items = []
    paths = myglob(path_glob)
    for i, path in enumerate(paths):
        items.extend(read_one(path))
        print(f"[read_parquet_or_jsonl] 读取文件{i+1}/{len(paths)}: {path} current_size: {len(items)}")
    return items

def write_parquet_or_jsonl(json_list, output_file):
    """ 写jsonl或者parquet文件，根据output_file的后缀来判断
    """
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    if output_file.endswith(".parquet"):
        # parquet文件 
        df = pd.DataFrame(json_list)
        logging.info("df: %s" %(df))
        # 将 DataFrame 转换为 PyArrow 表格
        table = pa.Table.from_pandas(df)
        # 将 PyArrow 表格写入 Parquet 文件
        pq.write_table(table, output_file)
        print("[*] write_parquet_or_jsonl 保存为parquet文件: %s" %(output_file))
    elif output_file.endswith(".csv"):
        # csv文件
        df = pd.DataFrame(json_list)
        df.to_csv(output_file, index=False)
    else:
        # jsonl 文件
        with open(output_file, 'w') as f:
            for item in json_list:
                json_line = json.dumps(item, ensure_ascii=False)
                f.write(json_line + '\n')
    return 
if __name__ == "__main__": 
    # print_json("")
    data = [{'name': '万事利', 'prev_rank': 1/3, 'prev_label': '-0.043', 'prev_pred': '0.051', 'next_rank': 171395, 'next_label': '-0.022', 'next_pred': '0.004'}, {'name': '万事利', 'prev_rank': 6861, 'prev_label': '0.002', 'prev_pred': '0.046', 'next_rank': 112013, 'next_label': '-0.006', 'next_pred': '0.012'}, {'name': '万兴科技', 'prev_rank': 1241, 'prev_label': '-0.035', 'prev_pred': '0.064', 'next_rank': 325567, 'next_label': '-0.083', 'next_pred': '-0.059'}, {'name': '万达信息', 'prev_rank': 2860, 'prev_label': '-0.037', 'prev_pred': '0.055', 'next_rank': 120407, 'next_label': '0.030', 'next_pred': '0.011'}, {'name': '三人行', 'prev_rank': 9714, 'prev_label': '0.064', 'prev_pred': '0.042', 'next_rank': 116845, 'next_label': '0.075', 'next_pred': '0.012'}]
    mprint(data)#, title = "陈剑峰cjf")
    # mprint([{"name": "cjf", "age" : 11}, {"name": "cjj", "age" : 22}], col_names=["age", "name"])
    # from google.protobuf.internal import api_implementation
    # print(api_implementation.Type())
    # # exit(0)

    # for ins in enum_instance("../../training_data/data.daily.20240120_0142"):
    #     pass