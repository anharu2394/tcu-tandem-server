
- `client/` - contains the client code for Tandem PC to send data to the server in Python
- `src/` - contains the gRPC server code in Go



- `client/` - contains the client code for Tandem PC to send data to the server in Python
- `src/` - contains the gRPC server code in Go


python3 -m grpc_tools.protoc  --python_out=. --pyi_out=. --grpc_python_out=. ../src/api/tandem.proto -I=../src/api


protoc \
  --go_out=../pkg/grpc \
  --go-grpc_out=../pkg/grpc \
  --go_opt=paths=source_relative \
  --go-grpc_opt=paths=source_relative \
 tandem.proto


protoc \
  --go_out=../pkg/grpc \
  --go-grpc_out=../pkg/grpc \
  --go_opt=paths=source_relative \
  --go-grpc_opt=paths=source_relative \
 tandem.proto


# 安定性指標の算出方法

スコア１－５はそれぞれ20点満点である。

## スコア1
GVMの分散を10点満点で評価する。
まず、0.0001以下が１０点、0.0002以下が８点、0.0004以下が7点、0.0005以下が６点、 0.001以下が４点、当てはまらないものは０点

GVM傾きを10点満点で評価する。
まず、0.001以下が１０点、0.002以下が８点、0.003以下が6点、0.004以下が4点、 0.005以下が2点、当てはまらないものは０点

この二つのスコアを足した値。

## スコア2
GVMとCPSの比に関する評価。
GVMとCPSの比の分散を10点満点で評価する。
まず、0.0001以下が１０点、0.00015以下が８点、0.0002以下が6、0.0003以下が4、 0.0004以下が2、当てはまらないものは０点

GVMとCPSの比の傾きを10点満点で評価する。
まず、0.0005以下が１０点、0.001以下が８点、0.002以下が6点、0.003以下が4点、 0.004以下が2点、当てはまらないものは０点
## スコア3
LE-HEについて。
-0.035以上が20、-0.04以上が18点、-0.05以上が16点、-0.06以上が14点、 -0.07以上が12点、-0.1以上が10点、 -0.15以上が8点、 -0.2以上が6点、- 0.25以上が4点、 当てはまらないものは０点
## スコア4
プローブカレントに関する評価。
プローブカレントの分散を10点満点で評価する。
まず、0.00001以下が１０点、0.00002以下が８点、0.00003以下が6、0.0001以下が4、 0.0002以下が2、当てはまらないものは０点

プローブカレントの傾きを10点満点で評価する。
まず、0.0001以下が１０点、0.00015以下が８点、0.0002以下が6、0.0003以下が4、 0.0004以下が2、当てはまらないものは０点
## スコア5
チャージカレントに関する評価。
チャージカレントの分散を10点満点で評価する。
まず、0.0004以下が１０点、0.0005以下が８点、0.0006以下が6、0.0007以下が4、 0.0008以下が2、当てはまらないものは０点

チャージカレントの傾きを10点満点で評価する。
まず、0.0005以下が１０点、0.001以下が８点、0.002以下が6点、0.003以下が4点、 0.004以下が2点、当てはまらないものは０点
## stability score
スコア１－５の合計