# pip install -r requirements.txt
# protobuf update
cd common
rm ./*_pb2.py
 ..\protoc-21.1-win64\bin\protoc.exe --python_out=./ ./stock.proto
