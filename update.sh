# pip install -r requirements.txt
# protobuf update
curPath=$(dirname "$0")
cd $curPath
# 编译stock.proto
cd src/common
rm *_pb2.py
protoc --python_out=./ ./stock.proto

cd $curPath