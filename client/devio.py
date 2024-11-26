class PyDevIo:

    def __init__(self, timeout):
        self.timeout = timeout

    #Open tcp
    def opentcp(self, IP, port):
        return True

    # Open usb
    def openusb(self, ID):
        return True

    #Close port
    def close(self):
        return True

    #Send command
    def send_command(self, strMsg):
        return True
    
    #Receive
    def read_command(self, timeout):
        return ""
    
    #Transmit and receive commands
    def send_read_command(self, strmsg, timeout):
        return ""

    def read_binary(self, readbytes, timeout):
        msgbuf = bytes(range(0))                    # Message buffer
        return msgbuf