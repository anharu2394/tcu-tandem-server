FROM golang:1.23.2 AS builder
RUN mkdir /app
ADD ./src /app
WORKDIR /app
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64  go build -o grpc ./cmd/server

FROM alpine:latest
COPY --from=builder /app ./
RUN chmod +x ./grpc
ENTRYPOINT ["./grpc"]
EXPOSE 8080