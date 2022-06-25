# pip install -r requirements.txt
cd run
rm ../common/stock_pb2.py
./protoc --python_out=../common ./stock.proto