import pandas as pd
import time
import asyncio
import os
from datetime import datetime, timedelta
from supabase import create_client, Client
import tandem_pb2
import tandem_pb2_grpc
import grpc
from google.protobuf import timestamp_pb2 as _timestamp_pb2
import uuid
import numpy as np
import struct

# Supabase setup
url = "https://kvsqxjeanrpifkcyvqkt.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2c3F4amVhbnJwaWZrY3l2cWt0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc2MzM0MDEsImV4cCI6MjA2MzIwOTQwMX0.5ah2atIUwHRoYh0xocXb-7FhSYeRVe_bLbGbGe46-08"
supabase: Client = create_client(url, key)

# gRPC setup
grpc_address = "tandem-grpc-server-hipd7dwdba-an.a.run.app:443"

# GBD path
gbd_path = "../gbd/GL240 01 Mar 26 2025.gbd"

def read_gbd_file(file_path):
    header_size = 9216
    record_size = 12 * 2

    with open(file_path, "rb") as f:
        f.seek(0, 2)
        file_size = f.tell()
        num_records = (file_size - header_size) // record_size
        f.seek(header_size)
        data_bytes = f.read(num_records * record_size)

    raw_data = np.frombuffer(data_bytes, dtype='>i2')
    data = raw_data.reshape((num_records, 12))
    analog_data_raw = data[:, :10]
    analog_data = analog_data_raw / 200.0

    time = np.arange(num_records) * 0.1
    channel_names = [
        "入射ファラデ電流",
        "加速後の電流",
        "Charge Current",
        "GVM",
        "Charge Power Supply",
        "LE",
        "HE",
        "C.P.O",
        "プローブカレント",
        "プローブポジション"
    ]
    df = pd.DataFrame(analog_data, columns=channel_names)
    df.insert(0, "Time(s)", time)
    return df

def process_gbd():
    df = read_gbd_file(gbd_path)
    return df.iloc[-30:]

async def send_to_grpc_forever():
    credentials = grpc.ssl_channel_credentials()
    async with grpc.aio.secure_channel(grpc_address, credentials) as channel:
        stub = tandem_pb2_grpc.TandemServiceStub(channel)

        async def generate_requests():
            last_row_count = 0
            while True:
                df = process_gbd()

                if len(df) != last_row_count:
                    print("GBDファイルが更新されました。")
                    for _, row in df.iterrows():
                        timestamp = datetime.utcnow()
                        timestamp_iso = timestamp.isoformat()
                        existing = supabase.table("tandem_data").select("id").eq("timestamp", timestamp_iso).execute()
                        if not existing.data:
                            supabase.table("tandem_data").insert({
                                "id": str(uuid.uuid4()),
                                "timestamp": timestamp_iso,
                                "beam_current_in": row["入射ファラデ電流"],
                                "beam_current_out": row["加速後の電流"],
                                "charge_current": row["Charge Current"],
                                "gvm": row["GVM"],
                                "charge_power_supply": row["Charge Power Supply"],
                                "le": row["LE"],
                                "he": row["HE"],
                                "cpo": row["C.P.O"],
                                "probe_current": row["プローブカレント"],
                                "probe_position": row["プローブポジション"]
                            }).execute()
                    last_row_count = len(df)

                if not df.empty:
                    latest_row = df.iloc[-1]
                    ts = _timestamp_pb2.Timestamp()
                    ts.FromDatetime(datetime.utcnow())
                    float_values = latest_row[1:].astype('float32').values.tobytes()
                    print("送信データ:", float_values)
                    yield tandem_pb2.SendDataRequest(message=float_values, timestamp=ts)
                await asyncio.sleep(1)

        try:
            response = await stub.SendData(generate_requests())
            print("gRPC応答:", response)
        except grpc.aio.AioRpcError as e:
            print(f"送信エラー: {e.code()} - {e.details()}")
        except asyncio.CancelledError:
            print("gRPCストリーム送信がCancelledErrorで中断されました。")

if __name__ == '__main__':
    asyncio.run(send_to_grpc_forever())
