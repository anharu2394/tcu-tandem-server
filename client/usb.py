from devio import PyDevIo
import clr
import time
clr.AddReference('DevIoManager')
from DevIoManagerSpace import DevIoManager

class Usb(PyDevIo):
    
    devio = None

    def __init__(self, timeout):
        super().__init__(timeout)

    def open(self, ID):
        self.devio = DevIoManager()
        ret = self.devio.OpenUsb(ID)
        print (ret)
        return ret

    def close(self):
        self.devio.Close()
        self.devio = None
        return

    # Send command
    def send_command(self, strmsg):
        ret = False
        try:
            strmsg = strmsg + '\r\n'                #Add a terminator, CR+LF, to transmitted command
            #print(strmsg)
            self.devio.SendCommand(strmsg, 1000)    #Convert to byte type and send
            ret = True
        except Exception as e:
            ret = False
        return ret
    
    # Read command
    def read_command(self, timeout):
        ret = False
        msgbuf = bytes(range(0))                    # Message buffer

        try:
            msgbuf  = self.devio.ReadCommand(timeout)     # Receive data from the device
            #print(msgbuf)
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
        return self.devio.ReadBinary(readbytes)


