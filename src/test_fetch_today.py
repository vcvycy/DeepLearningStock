import time
def timestamp2str(ts, format = "%Y%m%d"):
    return time.strftime(format,time.localtime(int(ts)))