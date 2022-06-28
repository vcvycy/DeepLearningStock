# pip install -r requirements.txt
# protobuf update
cd ../common
rm ./*_pb2.py
protoc --python_out=./ ./stock.proto
