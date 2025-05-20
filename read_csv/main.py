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

# Supabase setup
url = "https://kvsqxjeanrpifkcyvqkt.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2c3F4amVhbnJwaWZrY3l2cWt0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc2MzM0MDEsImV4cCI6MjA2MzIwOTQwMX0.5ah2atIUwHRoYh0xocXb-7FhSYeRVe_bLbGbGe46-08"
supabase: Client = create_client(url, key)

# gRPC setup
grpc_address = "tandem-grpc-server-hipd7dwdba-an.a.run.app:443"

# CSV path
csv_path = "csv.csv"

# Combine Time and ms into ISO timestamp
def parse_timestamp(row):
    base = datetime.strptime(row['Time'], "%Y/%m/%d %H:%M")
    return base + timedelta(milliseconds=int(row['ms']))

def process_csv():
    df = pd.read_csv(csv_path, encoding="utf-8", skiprows=29)
    df.columns = df.columns.str.strip()

    df['timestamp'] = df.apply(parse_timestamp, axis=1)

    df.rename(columns={
        'V': 'CH1', 'V.1': 'CH2', 'V.2': 'CH3', 'V.3': 'CH4',
        'V.4': 'CH5', 'V.5': 'CH6', 'V.6': 'CH7', 'V.7': 'CH8',
        'V.8': 'CH9', 'V.9': 'CH10'
    }, inplace=True)

    return df.iloc[-30:]

async def send_to_grpc_forever():
    credentials = grpc.ssl_channel_credentials()
    async with grpc.aio.secure_channel(grpc_address, credentials) as channel:
        stub = tandem_pb2_grpc.TandemServiceStub(channel)

        async def generate_requests():
            last_row_count = 0
            while True:
                df = process_csv()

                # Supabase登録（CSV行数が増えていればのみ実施）
                if len(df) != last_row_count:
                    for _, row in df.iterrows():
                        timestamp_iso = row['timestamp'].isoformat()
                        existing = supabase.table("tandem_data").select("id").eq("timestamp", timestamp_iso).execute()
                        if not existing.data:
                            supabase.table("tandem_data").insert({
                                "id": str(uuid.uuid4()),
                                "timestamp": timestamp_iso,
                                "beam_current_in": row['CH1'],
                                "beam_current_out": row['CH2'],
                                "charge_current": row['CH3'],
                                "gvm": row['CH4'],
                                "charge_power_supply": row['CH5'],
                                "le": row['CH6'],
                                "he": row['CH7'],
                                "cpo": row['CH8'],
                                "probe_current": row['CH9'],
                                "probe_position": row['CH10']
                            }).execute()
                    last_row_count = len(df)

                # 最新行をgRPCで送信（毎秒）
                if not df.empty:
                    latest_row = df.iloc[-1]
                    ts = _timestamp_pb2.Timestamp()
                    ts.FromDatetime(latest_row['timestamp'])
                    float_values = latest_row[['CH1','CH2','CH3','CH4','CH5','CH6','CH7','CH8','CH9','CH10']]\
                                    .astype('float32').values.tobytes()
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
