package main

import (
	"io"
	"log"
	"net"
	"os"
	"os/signal"
	tandempb "tandem-data-server/pkg/grpc"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"
	"google.golang.org/protobuf/types/known/emptypb"
)

func main() {
	// 1. 8080番portのListenerを作成
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
		log.Printf("Defaulting to port %s", port)
	}
	listener, err := net.Listen("tcp", ":"+port)
	if err != nil {
		panic(err)
	}
	/**
	cred, err := credentials.NewServerTLSFromFile("service.pem", "service.key")
	if err != nil {
		panic(err)
	}*/
	// 2. gRPCサーバーを作成
	s := grpc.NewServer()

	tandempb.RegisterTandemServiceServer(s, &tandemServer{})

	reflection.Register(s)
	go func() {
		log.Printf("start gRPC server port: %v", port)
		if err = s.Serve(listener); err != nil {
			log.Fatalf("failed to serve: %v", err)
		}
	}()

	// 4.Ctrl+Cが入力されたらGraceful shutdownされるようにする
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt)
	<-quit
	log.Println("stopping gRPC server...")
	s.GracefulStop()
}

type tandemServer struct {
	tandempb.UnimplementedTandemServiceServer
	prevSendDataRequest *tandempb.SendDataRequest
	currentSendDataRequest *tandempb.SendDataRequest
}

func (s *tandemServer) GetData(_ *emptypb.Empty,stream tandempb.TandemService_GetDataServer) error {
	for {
		prevTimestamp := s.prevSendDataRequest.GetTimestamp()
		currentTimestamp := s.currentSendDataRequest.GetTimestamp()
		if prevTimestamp != currentTimestamp {
			if err := stream.Send(&tandempb.GetDataResponse{Message: s.currentSendDataRequest.GetMessage()}); err != nil {
				log.Printf("Failed to send message: %v", err)
				return err
			}
		}
		s.prevSendDataRequest = s.currentSendDataRequest
		time.Sleep(1000 * time.Millisecond)
	}
}

func (s *tandemServer) SendData(stream tandempb.TandemService_SendDataServer) error {
	for {
		req, err := stream.Recv()
		if err != nil {
			if err == io.EOF {
				log.Printf("Client disconnected")
				return nil
			}
			log.Printf("Failed to receive message: %v", err)
			return err
		}
		s.currentSendDataRequest = req
	}
}
