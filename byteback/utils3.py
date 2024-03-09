import json
import os, sys
import re
# from utils import mprint
import concurrent.futures
import base64
import logging
from tqdm import tqdm
import subprocess
import yaml
"""
函数说明: 
1. print_json/compare_json: 打印/对比json数据
2. myglob: glob匹配hdfs或者本地文件
3. process_path: 如果是Hdfs路径, 则先下载,; 如果是本地路径, 则直接返回
4. get_files_recursive(dir, regexp) : 递归遍历文件夹, 匹配符合regexp条件的文件
5. read_parquet_or_jsonl/write_parquet_or_jsonl: 读写parquet、jsonl、csv文件，支持Hdfs路径
6. hf_download: 下载huggingface数据集
7. run_hsql: 执行sql查询
8. run_python: 本地执行python
9. MyTokerizer.encode/decode: tokenizer
"""
# class MyJson:
#     def __init__(self, json_path):
#         self.json_path = json_path
#         self.json = json.load(open(json_path))

#     def __str__(self):
#         return str(self.json)
#     def __ge

import re
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
                print(f"{'    '* dep}    {l}")
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
def compare_json(json1, json2):
    from deepdiff import DeepDiff
    diff = DeepDiff(json1, json2, ignore_order=True).to_dict()

    for change_type, changes in diff.items():
        print(f"\nChange type: {change_type}")
        for item_path, change in changes.items():
            print(f"Item path: {item_path}")
            print(f"Change: {change}")

def enum_ipynb_cell(ipynb_file):
    import nbformat
    with open(ipynb_file, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    for cell in nb.cells:
        yield cell
    return 

def myglob(path):
    """
      支持本地和hdfs
      给定一个path: 如
        1. *.json, 返回匹配的文件列表
        2. hdfs://haruna/xx/*.json
      返回匹配的路径
    """
    if "hdfs://" in path:
        from cruise.utilities.hdfs_io import hglob
        return hglob(path)
    else:
        import glob
        return glob.glob(path)
    return 

def get_md5(data):
    """计算MD5
    """
    import hashlib
    if isinstance(data, str):
        data = data.encode('utf-8')
    hash_md5 = hashlib.md5(data)
    return hash_md5.hexdigest()
def process_path(path):
    """
       如果是hdfs路径, 则先将其下载到本地，获取本地路径返回
    """
    if "hdfs://" in path:
        from cruise.utilities.hdfs_io import hcopy
        local_path = '/tmp/' + get_md5(path)[:10] + "_" + path.split('/')[-1]
        if not os.path.exists(local_path):
            print("文件不存在，开始从HDFS获取: %s -> %s" % (path, local_path))
            hcopy(path, local_path)
        else:
            print("文件 %s 存在" %(local_path))
        return local_path
    else:
        return path 

def get_related_files(item):
    # 枚举当前文件夹下的所有文件
    code = item['canonical_solution'] + item['test']
    cur_files = [f for f in os.listdir('.') if os.path.isfile(f)]
    # 初始化一个空列表来存储在code中找到的相关文件
    related_files = {}

    # 检查每个文件名是否出现在code字符串中
    for file in cur_files:
        if file in code:
            import base64
            related_files[file] = len(base64.b64encode(open(file, "rb").read()))
    # 返回相关文件列表
    return related_files
def get_files_recursive(directory, pattern=".*"):
    """
        枚举所有文件夹, 正则匹配
    """
    import re
    parquet_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            # print(file_path)
            if len(re.findall(pattern, file_path)) > 0:
                parquet_files.append(file_path) 
    return parquet_files

def print_highlight(s, p = None):
    """
      高亮输出s, 如果p不为空, 则高亮s中的子串p
    """
    if p is None:
        p = s
    start_tag = "\033[91m"  # 开始红色标记
    end_tag = "\033[0m"  # 结束标记
    
    idx = 0
    while idx < len(s):
        if s[idx:idx+len(p)] == p:
            print(start_tag + p + end_tag, end='')
            idx += len(p)
        else:
            print(s[idx], end='')
            idx += 1
    print() 
    return 
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

def hf_download(huggingface_path, save_path, name=None): 
    """
      用法: 
      hf_download("tianyang/repobench-c", "./hf_data/") 
      则会保存到: 
        mlxlab4bfuyt3064c8acc1-20230801065706-bvsxgd-master:mycode# ls hf_data/repobench-c/*
        hf_data/repobench-c/java_cff:
        total 150M
        -rw-r--r-- 1 root root  16M Sep  8 17:08 dev.parquet
        -rw-r--r-- 1 root root  16M Sep  8 17:08 test.parquet
        -rw-r--r-- 1 root root 119M Sep  8 17:08 train.parquet

        hf_data/repobench-c/java_cfr:
        total 52M
        -rw-r--r-- 1 root root 17M Sep  8 17:09 dev.parquet
        -rw-r--r-- 1 root root 17M Sep  8 17:09 test.parquet
        -rw-r--r-- 1 root root 18M Sep  8 17:08 train.parquet
        ....
    """
    import datasets
    from datasets import load_dataset,DownloadConfig
    def save_as_parquet(dataset, dir):
        if isinstance(dataset, datasets.DatasetDict):
            for key in dataset:
                cur_path = os.path.join(dir, key + ".parquet")
                print(f"处理文件: {cur_path}")
                dataset[key].to_parquet(cur_path)
        else:
            dataset.to_parquet(os.path.join(dir, "my.parquet")) 
        return 

    def download(huggingface_path, save_path, name = None):
        print(f"下载: {huggingface_path} {name} 到 {save_path}".center(100, "=")) 
        download_config = DownloadConfig(resume_download=True)
        dataset = load_dataset(path=huggingface_path,
                            name=name,
                            download_config=download_config) 
        save_path = os.path.join(save_path, huggingface_path.split("/")[-1], name if name is not None else "")
        os.makedirs(save_path, exist_ok=True)
        print(dataset)
        # dataset.save_to_disk(save_path)    # 这个存储为arrow
        save_as_parquet(dataset, save_path)  # 这个存储为parquet
        return 
    if name is None:
        try:
            download(huggingface_path, save_path)
        except Exception as e:
            print("[ERROR]: %s" %(e))
            exp_msg = [l for l in str(e).split("\n") if "Please pick one among" in l][0]
            avail_name = re.findall("'([^']+)'", exp_msg)
            print("将下载如下集合: %s" %(avail_name))
            input("..")
            for name in avail_name:
                download(huggingface_path, save_path, name)
    else:
        download(huggingface_path, save_path, name)
    return

def run_hsql(sql, to_dict = True):
    """
      运行hive
      文档: https://site.bytedance.net/docs/2137/tqs/273587/
      app_id/app_key: https://tqs.bytedance.net/#/apps
    """ 
    logging.getLogger("bytedtqs").setLevel(logging.WARNING)
    app_id = 'LXiqcUYEBnwia5pDO6gWzGqiq7EOj2xmDWfaQkg6Bijjsu83'
    app_key = "QTCesUL0e7kxWRqGrPzfLzy39XSPcjL1vCMA7yrxGlNlBIUY"
    user_name ="chenjianfeng.xmu"
    cluster = bytedtqs.Cluster.CN
    client = bytedtqs.TQSClient(app_id, app_key, cluster=cluster)
    job = client.execute_query(
            user_name,
            sql
    )
    if job.is_success():
        # 任务运行成功
        result = job.get_result().fetch_all_data()
        if to_dict:
            result = [dict(zip(result[0], row)) for row in result[1:]]
        return result
    else:
        # 任务运行异常，输出相关日志
        print(job.analysis_error_message())
        print(job.query_error_url)
        print(job.query_log_url)
        print(job.tracking_urls)
        raise Exception("sql执行是吧")
class MyTokenizer:
    """
       测试
            data = "hello, chenjianfeng"
            bbpe = "bbpe64k-0303" or "bbpe155k-v6.4.3-ml.pret" or "bbpe136k-v4.0"
            token_ids = MyTokenizer.encode(data, bbpe)
            print("token_ids: ", token_ids)
            print(MyTokenizer.decode(token_ids, bbpe))
    """
    name2tokenizer = {}
    @staticmethod
    def __get_tokenizer(bbpe_path):
        from transformers import AutoTokenizer  
        bbpe_path = f"{os.environ.get('MYCODE')}/aml/tokenizer/{bbpe_path}"
        name2tokenizer = MyTokenizer.name2tokenizer
        if bbpe_path not in name2tokenizer:
            path = process_path(bbpe_path)
            name2tokenizer[bbpe_path] = AutoTokenizer.from_pretrained(path)
        return name2tokenizer[bbpe_path]
    @staticmethod 
    def encode_batch(batch, bbpe_path="bbpe136k-v4.0"):
        # 创建线程池
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 提交任务到线程池
            futures = [executor.submit(MyTokenizer.encode, text, bbpe_path) for text in batch]
            # 获取结果
            progress_bar = tqdm(total=len(futures))  # 进度条
            results = []
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
                progress_bar.update(1)
            # results = [future.result() for future in concurrent.futures.as_completed(futures)]
        return results


    def decode_batch(batch, bbpe_path="bbpe136k-v4.0"):
        # 创建线程池
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 提交任务到线程池
            futures = [executor.submit(MyTokenizer.decode, token_ids, bbpe_path) for token_ids in batch]
            # 获取结果
            progress_bar = tqdm(total=len(futures))
            results = []
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
                progress_bar.update(1)
            # results = [future.result() for future in concurrent.futures.as_completed(futures)]
        return results

    @staticmethod
    def encode(text, bbpe_path="bbpe136k-v4.0"):
        tokenizer = MyTokenizer.__get_tokenizer(bbpe_path)
        return tokenizer.encode(text)
    @staticmethod
    def decode(ids, bbpe_path="bbpe136k-v4.0"):
        tokenizer = MyTokenizer.__get_tokenizer(bbpe_path)
        return tokenizer.decode(ids)
def run_python(code):
    try:
        # 创建一个用于捕获输出的临时文件对象
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()

        # 将代码写入临时文件
        with open(temp_file.name, 'w') as file:
            file.write(code)

        # 执行代码并捕获输出
        import subprocess
        result = subprocess.run(['python3', temp_file.name], capture_output=True, text=True)

        # 返回执行结果（包括输出和错误信息）
        return {
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except Exception as e:
        return {
            'error': str(e)
        }

def read_config_json_yaml(file_path):
    """读取配置文件: json或者yaml文件
    """
    file_path = process_path(file_path)
    _, ext = os.path.splitext(file_path)
    with open(file_path, 'r') as f:
        if ext == '.json':
            return json.load(f)
        elif ext in ('.yml', '.yaml'):
            return yaml.safe_load(f)
        else:
            raise ValueError('Unsupported file type')

def gpt_gpt_params(vocab_size, d_model, num_heads, num_layers, seq_len=0, ffw_size = -1,  is_rope=True):
    """ Given GPT config calculate total number of parameters 
        vocab_size: token数量
        d_model: 模型维度
        num_heads: 多头注意力head数
        num_layers: 层数
        seq_len: 用于计算absolut position embedding的参数，rope模式下不需要
        ffw_size: 默认为 4*d_model
    测试：
    gpt2 = dict(seq_len = 1024, vocab_size = 50257, d_model = 768, num_heads = 12, num_layers = 12)
    print(gpt_gpt_params(**gpt2)/1e6)
    """ 
    def show_p(p):
        if p > 1e9:
            return f"{p/1e9:.3f}G"
        else:
            return f"{p/1e6:.3f}M"
    if ffw_size == -1:
        ffw_size = 4*d_model  # MLPF扩大/缩小围度
    m = {
        "attn_qkv": 3 * d_model * d_model + 3 * d_model,
        "attn_proj" : d_model * d_model + d_model,
        "attn_mlpf" : ffw_size * d_model * 2 + d_model + ffw_size ,
        "attn_ln" : 2 * 2 * d_model,
        "out_ln" : 2 * d_model,           # 输出前的layer norm
        "output" : d_model * vocab_size,  # 输出nn
        # 下面两个不算进去: token embedding + pos embedding
        # "e_token": vocab_size * d_model,
        # "e_pos": seq_len * d_model if not is_rope else 0,
    } 
    print(m['attn_qkv'] + m['attn_proj'] + m['attn_mlpf'] + m['attn_ln'])
    show_p(num_layers * (m['attn_qkv'] + m['attn_proj'] + m['attn_mlpf'] + m['attn_ln']) )
    params = num_layers * (m['attn_qkv'] + m['attn_proj'] + m['attn_mlpf'] + m['attn_ln']) + m['out_ln'] + m['output']
    # params += m['e_token'] + m['e_pos'] 
    print("总参数: %s(不包含token/pos embedding), 分布:" %(show_p(params)))
    for key in m:
        p = m[key]
        if "attn" in key:
            p *= num_heads
        print(f"   * {key:10} 参数: %s 占比: %.2f%%" %(show_p(p), p/params*100))
    return params


gpt2 = dict(seq_len = 1024, vocab_size = 50257, d_model = 768, num_heads = 12, num_layers = 12)
print(gpt_gpt_params(**gpt2)/1e6)
exit(0)

def get_gpt_params_from_json(path):
    """
        get_gpt_params_from_json('/mlx_devbox/users/chenjianfeng.xmu/playground/evals/evals/test.json')
    """
    # path = process_path(path)   # hdfs支持
    # data = json.load(open(path))
    data = read_config_json_yaml(path)
    if 'model' in data:
        model = data['model']['network']
    else:
        model = data['network']
    vocab_size = model['vocab_size']
    d_model = model['n_embed']
    ffw_size = model.get('n_inner', -1)
    num_heads = model['n_head']
    num_layers = model['n_layer'] 
    return gpt_gpt_params(vocab_size = vocab_size, d_model = d_model, num_heads = num_heads, num_layers = num_layers, ffw_size = ffw_size)

def compare_command(cmd1, cmd2):
    """对比两个命令行的参数不同的地方
    """
    def parse_args(command):
        cmd = command.split("--")[0].strip() 
        pattern = re.compile(r"--([^=]+=[^ ]+)")
        matches = pattern.findall(command)
        params = {}
        for m in matches:
            kv = m.split("=")
            params[kv[0]] = kv[1]
        return cmd, params 
    def get_cmd2params(cmd):
        k = {}
        for c in cmd.split("&&"):
            if c.strip() == "":
                continue
            c, p = parse_args(c)
            k[c] = p
        return k
    c1params = get_cmd2params(cmd1)
    c2params = get_cmd2params(cmd2)
    keys = set(c1params) | set(c2params)
    rsps = []
    for k in keys:
        print("- 命令: %s" %(k))
        p1 = c1params.get(k, {})
        p2 = c2params.get(k, {})
        rsp = {
            "cmd" : k,
            "diff" : []
        }
        for p in set(p1) | set(p2):
            v1 = p1.get(p, "")
            v2 = p2.get(p, "")
            if v1!=v2:
                rsp['diff'].append({
                    'key' : p, 
                    "v1" : v1,
                    "v2" : v2
                })
                print("  --%s  【%s】【%s】" %(p, v1, v2))
        rsps.append(rsp)
    return rsps

if __name__ == "__main__":
    items = read_parquet_or_jsonl('hdfs://haruna/home/byte_data_seed/hl_lq/user/chenjianfeng.xmu/humaneval-multilang/humaneval-all.parquet')
    for item in items:
        del item['meta']['prompt_length']
    write_parquet_or_jsonl(items, "/tmp/humaneval-all-no-prompt-length.parquet")
    # list(enum_autoeval("/mlx_devbox/users/chenjianfeng.xmu/playground/code_data/eval/nl2code_cheminformatics_python.ipynb"))
    # exit(0)
    # print(len(list(enum_ipynb_cell("/mlx_devbox/users/chenjianfeng.xmu/playground/code_data/eval/nl2code_data_analysis_python/closeform_single/data_analysis_closeform_single.ipynb"))))
    # print(len(list(enum_ipynb_cell("/mlx_devbox/users/chenjianfeng.xmu/
    # path = '/mlx_devbox/users/chenjianfeng.xmu/playground/code_data/eval/nl2code_data_analysis_python/closeform_single/data_analysis_closeform_single.ipynb'
    # items = []
    # idx = 1
    # for p, c, t in enum_autoeval(path):
    #     idx +=1
    #     items.append({
    #         "idx" : idx,
    #         "prompt" :  len(MyTokenizer.encode(p, 'bbpe155k-v6.4.3-ml.pret')),
    #         "prompt+code" : len(MyTokenizer.encode(p + c, 'bbpe155k-v6.4.3-ml.pret'))
    #     })
    # items.sort(key = lambda x : -x['prompt'])
    # write_parquet_or_jsonl(items, "/tmp/sss.csv")
    # tot = {}
    # acc = {}
    # x  = 0
    # for cell in enum_ipynb_cell("./sprout.ipynb"):
    #     data = cell['source']
    #     import re 
    #     tmp = re.findall("## Task ID (.*)/\d+", data)
    #     if len(tmp ) == 0:
    #         continue
    #     task = tmp[0]
    #     # print(tmp[0])
    #     # input(".")
    #     tot[task] = tot.get(task, 0) + 1
    #     if "策略(选第一个ABCD的):Accepted" in data:
    #         acc[task] = acc.get(task, 0) + 1
    #     x+=1
    # keys = list(tot)
    # keys.sort(key = lambda x : x)
    # for k in keys:
    #     print("%s\t%.2f" %(k, acc.get(k, 0) / tot[k]))