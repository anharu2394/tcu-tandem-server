package main

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"strconv"
	"strings"
    "log"
	"math/rand"
	tandempb "tandem-data-server/pkg/grpc"
    timestamppb "google.golang.org/protobuf/types/known/timestamppb"
	"tandem-data-server/pkg/tcp"
	"time"

	"google.golang.org/grpc"
 	"google.golang.org/grpc/credentials/insecure"
)

var (
	client  tandempb.TandemServiceClient
)


// データパターンをバイトスライスとして定義
var dataPattern1 = []byte{
    // CH1〜CH20のアナログデータ（各2バイト）
    0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80, 0x90, 0xA0,
    0xB0, 0xC0, 0xD0, 0xE0, 0xF0, 0x00, 0x11, 0x22, 0x33, 0x44,
    0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE,
    0xFF, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09,

    // パルスデータ（各4バイト）
    0x00, 0x10, 0x00, 0x20,
    0x00, 0x30, 0x00, 0x40,
    0x00, 0x50, 0x00, 0x60,
    0x00, 0x70, 0x00, 0x80,

    // ロジックデータ（2バイト）
    0x01, 0x02,

    // アラームデータ 1（CH1〜CH10のアラームデータ：2バイト）
    0x03, 0x04,

    // アラームデータ 2（CH11〜CH20のアラームデータ：2バイト）
    0x05, 0x06,

    // アラームデータ (ロジック/パルス)（2バイト）
    0x07, 0x08,

    // アラーム出力データ（2バイト）
    0x09, 0x0A,

    // ステータスデータ（2バイト）
    0x0B, 0x0C,
}

var dataPattern2 = []byte{
    // CH1〜CH20のアナログデータ（各2バイト）
    0x0A, 0x1A, 0x2A, 0x3A, 0x4A, 0x5A, 0x6A, 0x7A, 0x8A, 0x9A,
    0xAA, 0xBA, 0xCA, 0xDA, 0xEA, 0xFA, 0x0A, 0x1B, 0x2B, 0x3B,
    0x4B, 0x5B, 0x6B, 0x7B, 0x8B, 0x9B, 0xAB, 0xBB, 0xCB, 0xDB,
    0xEB, 0xFB, 0x0B, 0x1C, 0x2C, 0x3C, 0x4C, 0x5C, 0x6C, 0x7C,

    // パルスデータ（各4バイト）
    0x10, 0x11, 0x10, 0x12,
    0x10, 0x13, 0x10, 0x14,
    0x10, 0x15, 0x10, 0x16,
    0x10, 0x17, 0x10, 0x18,

    // ロジックデータ（2バイト）
    0xA1, 0xB2,

    // アラームデータ 1（CH1〜CH10のアラームデータ：2バイト）
    0xC1, 0xD2,

    // アラームデータ 2（CH11〜CH20のアラームデータ：2バイト）
    0xE1, 0xF2,

    // アラームデータ (ロジック/パルス)（2バイト）
    0x21, 0x22,

    // アラーム出力データ（2バイト）
    0x31, 0x32,

    // ステータスデータ（2バイト）
    0x41, 0x42,
}

var dataPattern3 = []byte{
    // CH1〜CH20のアナログデータ（各2バイト）
    0x11, 0x21, 0x31, 0x41, 0x51, 0x61, 0x71, 0x81, 0x91, 0xA1,
    0xB1, 0xC1, 0xD1, 0xE1, 0xF1, 0x01, 0x12, 0x22, 0x32, 0x42,
    0x52, 0x62, 0x72, 0x82, 0x92, 0xA2, 0xB2, 0xC2, 0xD2, 0xE2,
    0xF2, 0x02, 0x13, 0x23, 0x33, 0x43, 0x53, 0x63, 0x73, 0x83,

    // パルスデータ（各4バイト）
    0x20, 0x21, 0x20, 0x22,
    0x20, 0x23, 0x20, 0x24,
    0x20, 0x25, 0x20, 0x26,
    0x20, 0x27, 0x20, 0x28,

    // ロジックデータ（2バイト）
    0xB1, 0xC2,

    // アラームデータ 1（CH1〜CH10のアラームデータ：2バイト）
    0xD1, 0xE2,

    // アラームデータ 2（CH11〜CH20のアラームデータ：2バイト）
    0xF1, 0x02,

    // アラームデータ (ロジック/パルス)（2バイト）
    0x12, 0x23,

    // アラーム出力データ（2バイト）
    0x34, 0x45,

    // ステータスデータ（2バイト）
    0x56, 0x67,
}

var dataPatterns = [][]byte{dataPattern1, dataPattern2, dataPattern3}

func main() {
    ifTcp(1 * time.Second)
}

// TCP/IP Connection Handler
func ifTcp(timeout time.Duration) {
    ip := "tandem-grpc-server-hipd7dwdba-an.a.run.app"
    port := 80
	address := ip + ":" + strconv.Itoa(port)
    log.Println("start")
	conn, err := grpc.Dial(
		address,

		grpc.WithTransportCredentials(insecure.NewCredentials()),
	//	grpc.WithBlock(),
	)
	if err != nil {
        log.Println(err)
		log.Fatal("Connection failed.")
		return
	}
    log.Println("start connect")
	defer conn.Close()

	// 3. gRPCクライアントを生成
	client = tandempb.NewTandemServiceClient(conn)

    tcp := tcp.NewTcp(timeout)
    if !tcp.Open(ip, port) {
        fmt.Println("Connection error")
        return
    }
    defer tcp.Close()

    sendData(tcp)


    mode := 0

    if mode == 0 {
        asciiMode(tcp)
    } else {
        binaryMode(tcp)
    }
}

// ASCII Mode Communication
func asciiMode(tcp *tcp.Tcp) {
    scanner := bufio.NewScanner(os.Stdin)
    for {
        fmt.Println("Enter the command (Exit with no input) Ex.*IDN?")
        scanner.Scan()
        command := scanner.Text()
        if command == "" {
            break
        }
        if strings.Contains(command, "?") {
            response, success := tcp.SendReadCommand(command)
            if success {
                fmt.Println(response)
            }
        } else {
            tcp.SendCommand(command)
        }
    }
}

// Binary Mode Communication
func binaryMode(tcp *tcp.Tcp) {
    stream, err := client.SendData(context.Background())
    if err != nil {
        fmt.Println(err)
        return
    }
    for {
        command := ":MEAS:OUTP:ONE?"
        if command == "" {
            break
        }
        tcp.SendCommand(command)
        if strings.Contains(command, "?") {
            header, _ := tcp.ReadBinary(8)
            fmt.Println("Header:", string(header))
            length, _ := strconv.Atoi(string(header[2:8]))
            fmt.Printf("Length: %d\n", length)
            data, _ := tcp.ReadBinary(length)
            err := stream.Send(&tandempb.SendDataRequest{Message: data, Timestamp: timestamppb.New(time.Now())})
            if err != nil {
                fmt.Println(err)
            }
            fmt.Println("Data:", data)
        }
        time.Sleep(1 * time.Second)
    }
}

func sendData(tcp *tcp.Tcp) {
    fmt.Println("start send data")
    stream, err := client.SendData(context.Background())
    if err != nil {
        fmt.Println(err)
        return
    }
    for {
        fmt.Println("send data")
        data := randomData()
        err := stream.Send(&tandempb.SendDataRequest{Message: data, Timestamp: timestamppb.New(time.Now())})
        if err != nil {
            fmt.Println(err)
        }
        fmt.Println("Data:", data)
        time.Sleep(1 * time.Second)
    }
}

func randomData() []byte {
    rand.Seed(time.Now().UnixNano())
    return dataPatterns[rand.Intn(len(dataPatterns))]
}