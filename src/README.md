protoc --go_out=../pkg/grpc --go_opt=paths=source_relative \
        --go-grpc_out=../pkg/grpc --go-grpc_opt=paths=source_relative \
        tandem.proto

cd client
python -m grpc_tools.protoc -I../src/api  --python_out=. --pyi_out=. --grpc_python_out=. ../src/api/tandem.proto

pip install pythonnet grpcio-tools grpcio

 docker build -t  asia-northeast1-docker.pkg.dev/tcu-tandem/tandem-grpc-server/image:latest .
 docker push  asia-northeast1-docker.pkg.dev/tcu-tandem/tandem-grpc-server/image:latest

 gcloud run deploy --image  asia-northeast1-docker.pkg.dev/tcu-tandem/tandem-grpc-server/image:latest --platform=managed --region asia-northeast1 --use-http2 --allow-unauthenticated --port 8080  tandem-grpc-server
 