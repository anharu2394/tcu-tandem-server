package tcp

import (
    "bufio"
    "bytes"
    "fmt"
    "net"
    "strings"
    "time"
)

// Tcp struct with connection parameters
type Tcp struct {
    conn    net.Conn
    timeout time.Duration
}

// NewTcp initializes the TCP connection with a timeout
func NewTcp(timeout time.Duration) *Tcp {
    return &Tcp{timeout: timeout}
}

// Open a TCP connection
func (t *Tcp) Open(ip string, port int) bool {
    addr := fmt.Sprintf("%s:%d", ip, port)
    conn, err := net.DialTimeout("tcp", addr, t.timeout)
    if err != nil {
        fmt.Println("Connection error:", err)
        return false
    }
    t.conn = conn
    return true
}

// Close the TCP connection
func (t *Tcp) Close() bool {
    if t.conn != nil {
        err := t.conn.Close()
        if err != nil {
            fmt.Println("Error closing connection:", err)
            return false
        }
    }
    return true
}

// SendCommand sends a command over TCP
func (t *Tcp) SendCommand(command string) bool {
    if t.conn == nil {
        return false
    }
    command += "\r\n"
    _, err := t.conn.Write([]byte(command))
    if err != nil {
        fmt.Println("Error sending command:", err)
        return false
    }
    return true
}

// ReadCommand reads a response from the TCP connection
func (t *Tcp) ReadCommand() (string, bool) {
    if t.conn == nil {
        return "", false
    }
    t.conn.SetReadDeadline(time.Now().Add(t.timeout))
    reader := bufio.NewReader(t.conn)
    response, err := reader.ReadString('\n')
    if err != nil {
        fmt.Println("Error reading response:", err)
        return "", false
    }
    return strings.TrimSpace(response), true
}

// SendReadCommand sends a command and reads the response
func (t *Tcp) SendReadCommand(command string) (string, bool) {
    if t.SendCommand(command) {
        return t.ReadCommand()
    }
    return "", false
}

// ReadBinary reads binary data from the connection
func (t *Tcp) ReadBinary(readBytes int) ([]byte, bool) {
    if t.conn == nil {
        return nil, false
    }
    buffer := make([]byte, readBytes)
    t.conn.SetReadDeadline(time.Now().Add(t.timeout))
    _, err := t.conn.Read(buffer)
    if err != nil {
        fmt.Println("Error reading binary data:", err)
        return nil, false
    }
    return bytes.Trim(buffer, "\r"), true
}
