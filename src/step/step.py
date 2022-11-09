from common.utils import *
import time
class Step:
    def __init__(self, conf):
        self.conf = conf
        self.time_cost = 0
        pass
    
    def _execute(self, context):
        raise Exception("_execute need override")
        return 

    def execute(self, context):
        ts = time.time()
        self._execute(context)
        self.time_cost += time.time() - ts
        return 