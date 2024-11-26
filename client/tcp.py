# coding: UTF-8

from devio import PyDevIo
import socket
import time

BUFFSIZE = 8192

class Tcp(PyDevIo):

    # Constractor
    def __init__(self, timeout):
        super().__init__(timeout)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        self.sock.settimeout(timeout)                                   #Timeout

    # Open socket
    def open(self, IP, port):
        ret = False

        try:
            self.sock.connect((IP, port))
            ret = True
        except Exception as e:
            ret = False
        
        return ret

    # Close socket
    def close(self):
        ret = False

        try:
            self.sock.close()
            ret = True
        except Exception as e:
            ret = False
        
        return ret

    # Send command
    def send_command(self, strmsg):
        ret = False

        try:
            strmsg = strmsg + '\r\n'                #Add a terminator, CR+LF, to transmitted command
            self.sock.send(bytes(strmsg, 'utf-8'))  #Convert to byte type and send
            ret = True
        except Exception as e:
            ret = False

        return ret
    
    # Read command
    def read_command(self, timeout):
        ret = False
        msgbuf = bytes(range(0))                    # Message buffer

        try:
            start = time.time()                     # Record for timeout
            while True:
                rcv  = self.sock.recv(BUFFSIZE)     # Receive data from the device
                rcv = rcv.strip(b"\r")              # Delete CR in received data
                if b"\n" in rcv:                    # End the loop when LF is received
                    rcv = rcv.strip(b"\n")          # Ignore the terminator CR
                    msgbuf = msgbuf + rcv
                    msgbuf = msgbuf.decode('utf-8')
                    break
                else:
                    msgbuf = msgbuf + rcv
                
                #Timeout processing
                if  time.time() - start > timeout:
                    msgbuf = ""
                    break
        except Exception as e:
            ret = False

        return msgbuf
    
    # send and read commands
    def send_read_command(self, strmsg, timeout):
        ret = self.send_command(strmsg)
        if ret:
            msgbuf_str = self.read_command(timeout)  #Receive response when command transmission is succeeded
        else:
            msgbuf_str = ""

        return msgbuf_str

    # Read binary
    def read_binary(self, readbytes, timeout):
        ret = False
        msgbuf = bytes(range(0))                # Message buffer

        try:
            rcv  = self.sock.recv(readbytes)    # Receive data from the device
            rcv = rcv.strip(b"\r")              # Delete CR in received data
            msgbuf = msgbuf + rcv
            
        except Exception as e:
            ret = False

        return msgbuf