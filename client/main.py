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
import asyncio
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2

#Timeout(1sec)
Timeout_default = 1

async def main():
    await if_usb()
# USB Connection
async def if_usb():


    ID = 0

    usb = Usb(Timeout_default)
    if not usb.open(ID):
        print("Connection error")
        return

    await binary_mode(usb)

    usb.close()

# Binary mode
async def binary_mode(obj):
    credentials = grpc.ssl_channel_credentials()
    async with grpc.aio.secure_channel("tandem-grpc-server-hipd7dwdba-an.a.run.app:443",credentials) as channel:
        stub = tandem_pb2_grpc.TandemServiceStub(channel)
        #Send and receive commands
        response = await stub.SendData(binary_generator(obj))
        print(response)

async def binary_generator(obj):
    try:
        while True:
            command = ":MEAS:OUTP:ONE?"
            
            # Send command
            if not obj.send_command(command):
                print("コマンド送信エラー")
                break

            try:
                msgbuf = bytes(obj.read_binary(8, Timeout_default))
                if not msgbuf:
                    print("ヘッダー読み取りエラー")
                    break
                    
                length = int(msgbuf[2:8].decode('utf-8'))
                msgbuf2 = obj.read_binary(length, Timeout_default)
                
                timestamp = _timestamp_pb2.Timestamp(seconds=int(time.time()))
                yield tandem_pb2.SendDataRequest(message=bytes(msgbuf2), timestamp=timestamp)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"データ読み取りエラー: {e}")
                break
                
    except Exception as e:
        print(f"予期せぬエラー: {e}")
        raise

if __name__ == '__main__':
  asyncio.run(main())
