# coding: UTF-8
"""
This program is a sample program that controls Graphtec GL series by Python.
The connection supports USB and TCP/IP(LAN) connection.
(* USB connection is Windows OS only)
Refer to the SDK specifications for the commands that can be entered. It does not support binary commands.

System requirements (software)
    Python 3.8

Required packages
    pythonnet (for USB connection)
"""

from usb import Usb
import time
import grpc
import tandem_pb2
import tandem_pb2_grpc
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2

#Timeout(1sec)
Timeout_default = 1

def main():
    if_usb()
# USB Connection
def if_usb():

    print("USB ID of the device?")
    ID = int(input())

    usb = Usb(Timeout_default)
    if not usb.open(ID):
        print("Connection error")
        return

    binary_mode(usb)

    usb.close()

# Binary mode
async def binary_mode(obj):
    async with grpc.aio.insecure_channel("tandem-grpc-server-hipd7dwdba-an.a.run.app:443") as channel:
        stub = tandem_pb2_grpc.TandemStub(channel)
        #Send and receive commands
        stream = stub.SendData(google_dot_protobuf_dot_empty__pb2.Empty())
        while True:
            command = ":MEAS:OUTP:ONE?"
            
            # Send command
            obj.send_command(command)

            #If the command contains "?"
            msgbuf = obj.read_binary(8, Timeout_default)    # Read header
            print(msgbuf.decode())
            len = int(msgbuf[2:8].decode('utf-8'))          # Read binary byte length
            print("Len " + str(len))
            msgbuf2 = obj.read_binary(len, Timeout_default) # Read data
            print(msgbuf2, type(msgbuf2))
            timestamp = _timestamp_pb2.Timestamp(seconds=int(time.time()))
            request = tandem_pb2.SendDataRequest(message=msgbuf2, timestamp=timestamp)
            stream.write(request)
            #Send only
            time.sleep(1)


if __name__ == '__main__':
  main()
