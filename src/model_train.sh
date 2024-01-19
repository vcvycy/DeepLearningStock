#!/bin/bash

# 获取 python main.py 的进程ID
pid=$(pgrep -f "main.py")

# 如果获取到 PID，等待其进程结束
if [[ -n $pid ]]; then
    while kill -0 $pid > /dev/null 2>&1; do
        echo "Waiting for python main.py to finish..."
        sleep 5
    done
fi

# 执行下一个命令
echo "Python script has completed, running the next command..."
python model_train.py
