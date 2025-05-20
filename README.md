
- `client/` - contains the client code for Tandem PC to send data to the server in Python
- `src/` - contains the gRPC server code in Go


python3 -m grpc_tools.protoc  --python_out=. --grpc_python_out=. ../src/api/tandem.proto -I=../src/api


protoc \
  --go_out=../pkg/grpc \
  --go-grpc_out=../pkg/grpc \
  --go_opt=paths=source_relative \
  --go-grpc_opt=paths=source_relative \
 tandem.proto