from common.utils import *
from common import sqlite3_api 
from step.step import Step
import sqlite3
import time
import struct
from queue import Queue
import threading
import json
import logging
class WriteSQLite3Step(Step):
    def __init__(self, conf):
        super(WriteSQLite3Step, self).__init__(conf) 
        self.cache = Queue()
        self.cache_size = conf.get("cache_size", 30)  
        print("cache_size: %s" %(self.cache_size))
        self.last_write_time = time.time()  # 最后一次写文件的时间
        self.write_mutex = threading.Lock()
        self.write_count = 0
        return 

    def write_instance(self):
        self.write_mutex.acquire()
        # 把二进制数据+字节数写到文件中: 写到队列为空或者写cache个
        self.last_write_time = time.time()
        instances = []
        for _ in range(self.cache_size):
            if self.cache.empty():
                break
            instances.append(self.cache.get())
        if len(instances) > 0:
            self.write_count += len(instances)
            sqlite3_api.write_instances(instances)
            print("write sqlite total %s" %(self.write_count))
        self.write_mutex.release()
        return  

    def _execute(self, context):  
        self.cache.put(context.get("pack_instance"))
        # cache数足够了，则写文件
        if self.cache.qsize() >= self.cache_size or (self.cache.qsize() > 0 and self.last_write_time < time.time() -10):
            self.write_instance()
        return 
