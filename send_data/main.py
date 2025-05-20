import pandas as pd
import time
import asyncio
import os
from datetime import datetime
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
grpc_address = "127.0.0.1:8080"

# GBD path
gbd_path = '../gbd/GL240 01 Mar 26 2025.gbd'

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
    analog_data_raw = data[:, :10] / 200.0

    time_sec = np.arange(num_records) * 0.1
    columns = [
        "入射ファラデ電流", "加速後の電流", "Charge Current", "GVM", "Charge Power Supply",
        "LE", "HE", "C.P.O", "プローブカレント", "プローブポジション"
    ]
    df = pd.DataFrame(analog_data_raw, columns=columns)
    df.insert(0, "Time(s)", time_sec)
    return df

def calc_slope_variance(series):
    x = np.arange(len(series))
    y = series.values
    slope = np.polyfit(x, y, 1)[0] if len(series) > 1 else 0.0
    variance = float(np.var(y))
    return slope, variance

def calc_stability_score(*metrics):
    return float(np.mean(metrics))

async def send_to_grpc():
    credentials = grpc.ssl_channel_credentials()
    while True:  # 永続的な接続を維持
        try:
            async with grpc.aio.secure_channel(
                "tandem-grpc-server-hipd7dwdba-an.a.run.app:443",
                credentials
            ) as channel:
                stub = tandem_pb2_grpc.TandemServiceStub(channel)
                print("gRPC接続を開始します")
                
                # ストリームを開始
                stream = stub.SendData()
                
                while True:  # 単一のストリーム内で継続的にデータを送信
                    try:
                        df = read_gbd_file(gbd_path)
                        if len(df) < 100:
                            await asyncio.sleep(1)
                            continue

                        recent_df = df.iloc[-100:]
                        latest_row = recent_df.iloc[-1]

                        # 各指標計算
                        transmission = recent_df["加速後の電流"] / recent_df["入射ファラデ電流"].replace(0, np.nan)
                        transmission_slope, transmission_variance = calc_slope_variance(transmission.fillna(0))

                        charge_current_slope, charge_current_variance = calc_slope_variance(recent_df["Charge Current"])
                        gvm_float_series = recent_df["GVM"].astype(float)
                        gvm_slope, gvm_variance = calc_slope_variance(gvm_float_series)

                        charge_supply_series = recent_df["Charge Power Supply"]
                        gvm_charge_diff = gvm_float_series - charge_supply_series
                        gvm_charge_slope, gvm_charge_variance = calc_slope_variance(gvm_charge_diff)
                        gvm_charge_correlation = float(np.corrcoef(gvm_float_series, charge_supply_series)[0, 1]) if len(gvm_float_series) > 1 else 0

                        stability_score = calc_stability_score(
                            transmission_slope,
                            transmission_variance,
                            charge_current_slope,
                            charge_current_variance,
                            gvm_slope,
                            gvm_variance
                        )

                        timestamp = datetime.utcnow()
                        timestamp_proto = _timestamp_pb2.Timestamp()
                        timestamp_proto.FromDatetime(timestamp)

                        tandem_data = tandem_pb2.TandemData(
                            id=str(uuid.uuid4()),
                            timestamp=timestamp_proto,
                            beam_current_in=latest_row["入射ファラデ電流"],
                            beam_current_out=latest_row["加速後の電流"],
                            charge_current=latest_row["Charge Current"],
                            gvm=str(latest_row["GVM"]),
                            charge_power_supply=latest_row["Charge Power Supply"],
                            le=latest_row["LE"],
                            he=latest_row["HE"],
                            cpo=latest_row["C.P.O"],
                            probe_current=latest_row["プローブカレント"],
                            probe_position=latest_row["プローブポジション"],
                            experiment_id="",
                            transmission_ratio=latest_row["加速後の電流"] / latest_row["入射ファラデ電流"] if latest_row["入射ファラデ電流"] != 0 else 0,
                            transmission_slope=transmission_slope,
                            transmission_variance=transmission_variance,
                            beam_loss_ratio=latest_row["HE"] / latest_row["LE"] if latest_row["LE"] != 0 else 0,
                            gvm_charge_slope=gvm_charge_slope,
                            gvm_charge_variance=gvm_charge_variance,
                            gvm_charge_correlation=gvm_charge_correlation,
                            charge_current_slope=charge_current_slope,
                            charge_current_variance=charge_current_variance,
                            gvm_slope=gvm_slope,
                            gvm_variance=gvm_variance,
                            stability_score=stability_score
                        )

                        print("送信データ:", tandem_data)
                        
                        # 同じストリームにデータを送信
                        await stream.write(tandem_data)

                        # Supabase送信（同じtimestampが登録済みならスキップ）
                        existing = supabase.table("tandem_data").select("id").eq("timestamp", timestamp.isoformat()).execute()
                        if not existing.data:
                            supabase.table("tandem_data").insert({
                                "id": tandem_data.id,
                                "timestamp": timestamp.isoformat(),
                                "beam_current_in": tandem_data.beam_current_in,
                                "beam_current_out": tandem_data.beam_current_out,
                                "charge_current": tandem_data.charge_current,
                                "gvm": tandem_data.gvm,
                                "charge_power_supply": tandem_data.charge_power_supply,
                                "le": tandem_data.le,
                                "he": tandem_data.he,
                                "cpo": tandem_data.cpo,
                                "probe_current": tandem_data.probe_current,
                                "probe_position": tandem_data.probe_position,
                                "transmission_ratio": tandem_data.transmission_ratio,
                                "transmission_slope": tandem_data.transmission_slope,
                                "transmission_variance": tandem_data.transmission_variance,
                                "beam_loss_ratio": tandem_data.beam_loss_ratio,
                                "gvm_charge_slope": tandem_data.gvm_charge_slope,
                                "gvm_charge_variance": tandem_data.gvm_charge_variance,
                                "gvm_charge_correlation": tandem_data.gvm_charge_correlation,
                                "charge_current_slope": tandem_data.charge_current_slope,
                                "charge_current_variance": tandem_data.charge_current_variance,
                                "gvm_slope": tandem_data.gvm_slope,
                                "gvm_variance": tandem_data.gvm_variance,
                                "stability_score": tandem_data.stability_score
                            }).execute()
                        else:
                            print("⚠️ Supabase: 同じtimestampのデータが既に存在するためスキップされました。")

                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        print(f"データ送信エラー: {e} - 1秒後に再試行します")
                        await asyncio.sleep(1)
                        continue
                
        except Exception as e:
            print(f"gRPC接続エラー: {e}")
            print("5秒後に再接続を試みます...")
            await asyncio.sleep(5)  # エラー時に5秒待機して再接続

if __name__ == '__main__':
    asyncio.run(send_to_grpc())
