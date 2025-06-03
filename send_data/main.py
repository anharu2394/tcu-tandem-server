import pandas as pd
import time
import asyncio
import os
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
import tandem_pb2
import tandem_pb2_grpc
import grpc
from google.protobuf import timestamp_pb2 as _timestamp_pb2
import uuid
import numpy as np
import struct
import socket

# Supabase setup
url = "https://kvsqxjeanrpifkcyvqkt.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2c3F4amVhbnJwaWZrY3l2cWt0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc2MzM0MDEsImV4cCI6MjA2MzIwOTQwMX0.5ah2atIUwHRoYh0xocXb-7FhSYeRVe_bLbGbGe46-08"

try:
    supabase: Client = create_client(url, key)
    print("Supabase接続を開始します")
except Exception as e:
    print(f"Supabase接続エラー: {e}")
    print("Supabaseへの接続に失敗しました。データベースへの保存はスキップされます。")
    supabase = None

# gRPC setup
grpc_address = "tandem-grpc-server-hipd7dwdba-an.a.run.app:443"

def get_gbd_path():
    today = datetime.now()
    # 日付フォーマット: YYYY-MM-DD
    date_str = today.strftime("%Y-%m-%d")
    base_path = r"C:\Users\TCU-Tandem\Documents\graphtec\GL100_240_840-APS\Data\2024-12-10"
    
    # 今日の日付フォルダのパスを作成
    date_path = os.path.join(base_path, date_str)
    
    # フォルダが存在しない場合は作成
    if not os.path.exists(date_path):
        os.makedirs(date_path)
        print(f"新しいフォルダを作成しました: {date_path}")
        return None
    
    # フォルダ内のGBDファイルを検索
    gbd_files = [f for f in os.listdir(date_path) if f.endswith('.gbd')]
    
    if not gbd_files:
        print(f"フォルダ内にGBDファイルが見つかりません: {date_path}")
        return None
    
    # 最新のファイルを取得（ファイル名の日時でソート）
    latest_file = sorted(gbd_files)[-1]
    latest_path = os.path.join(date_path, latest_file)
    
    print(f"最新のGBDファイルを開きます: {latest_path}")
    return latest_path

# 初期のGBDパスを設定
gbd_path = get_gbd_path()

def read_gbd_file(file_path):
    if file_path is None:
        print("GBDファイルが見つかりません。新しいファイルを作成します。")
        return pd.DataFrame()  # 空のDataFrameを返す
    
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

def calc_score1(gvm_variance, gvm_slope):
    # GVM分散の評価（10点満点）
    if gvm_variance <= 0.0001:
        variance_score = 10
    elif gvm_variance <= 0.0002:
        variance_score = 8
    elif gvm_variance <= 0.0004:
        variance_score = 7
    elif gvm_variance <= 0.0005:
        variance_score = 6
    elif gvm_variance <= 0.001:
        variance_score = 4
    else:
        variance_score = 0

    # GVM傾きの評価（10点満点）
    if gvm_slope <= 0.001:
        slope_score = 10
    elif gvm_slope <= 0.002:
        slope_score = 8
    elif gvm_slope <= 0.003:
        slope_score = 6
    elif gvm_slope <= 0.004:
        slope_score = 4
    elif gvm_slope <= 0.005:
        slope_score = 2
    else:
        slope_score = 0

    return variance_score + slope_score

def calc_score2(gvm_charge_variance, gvm_charge_slope):
    # GVMとCPSの比の分散の評価（10点満点）
    if gvm_charge_variance <= 0.0001:
        variance_score = 10
    elif gvm_charge_variance <= 0.00015:
        variance_score = 8
    elif gvm_charge_variance <= 0.0002:
        variance_score = 6
    elif gvm_charge_variance <= 0.0003:
        variance_score = 4
    elif gvm_charge_variance <= 0.0004:
        variance_score = 2
    else:
        variance_score = 0

    # GVMとCPSの比の傾きの評価（10点満点）
    if gvm_charge_slope <= 0.0005:
        slope_score = 10
    elif gvm_charge_slope <= 0.001:
        slope_score = 8
    elif gvm_charge_slope <= 0.002:
        slope_score = 6
    elif gvm_charge_slope <= 0.003:
        slope_score = 4
    elif gvm_charge_slope <= 0.004:
        slope_score = 2
    else:
        slope_score = 0

    return variance_score + slope_score

def calc_score3(le_he_difference):
    # LE-HEの評価（20点満点）
    if le_he_difference >= -0.035:
        return 20
    elif le_he_difference >= -0.04:
        return 18
    elif le_he_difference >= -0.05:
        return 16
    elif le_he_difference >= -0.06:
        return 14
    elif le_he_difference >= -0.07:
        return 12
    elif le_he_difference >= -0.1:
        return 10
    elif le_he_difference >= -0.15:
        return 8
    elif le_he_difference >= -0.2:
        return 6
    elif le_he_difference >= -0.25:
        return 4
    else:
        return 0

def calc_score4(probe_current_variance, probe_current_slope):
    # プローブカレントの分散の評価（10点満点）
    if probe_current_variance <= 0.00001:
        variance_score = 10
    elif probe_current_variance <= 0.00002:
        variance_score = 8
    elif probe_current_variance <= 0.00003:
        variance_score = 6
    elif probe_current_variance <= 0.0001:
        variance_score = 4
    elif probe_current_variance <= 0.0002:
        variance_score = 2
    else:
        variance_score = 0

    # プローブカレントの傾きの評価（10点満点）
    if probe_current_slope <= 0.0001:
        slope_score = 10
    elif probe_current_slope <= 0.00015:
        slope_score = 8
    elif probe_current_slope <= 0.0002:
        slope_score = 6
    elif probe_current_slope <= 0.0003:
        slope_score = 4
    elif probe_current_slope <= 0.0004:
        slope_score = 2
    else:
        slope_score = 0

    return variance_score + slope_score

def calc_score5(charge_current_variance, charge_current_slope):
    # チャージカレントの分散の評価（10点満点）
    if charge_current_variance <= 0.00001:
        variance_score = 10
    elif charge_current_variance <= 0.00002:
        variance_score = 8
    elif charge_current_variance <= 0.00003:
        variance_score = 6
    elif charge_current_variance <= 0.0001:
        variance_score = 4
    elif charge_current_variance <= 0.0002:
        variance_score = 2
    else:
        variance_score = 0

    # チャージカレントの傾きの評価（10点満点）
    if charge_current_slope <= 0.0005:
        slope_score = 10
    elif charge_current_slope <= 0.001:
        slope_score = 8
    elif charge_current_slope <= 0.002:
        slope_score = 6
    elif charge_current_slope <= 0.003:
        slope_score = 4
    elif charge_current_slope <= 0.004:
        slope_score = 2
    else:
        slope_score = 0

    return variance_score + slope_score

def calc_stability_score(score1, score2, score3, score4, score5):
    return score1 + score2 + score3 + score4 + score5

async def generate_tandem_data():
    while True:
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

            # 新しい指標の計算
            probe_current_slope, probe_current_variance = calc_slope_variance(recent_df["プローブカレント"])
            le_he_difference = latest_row["LE"] - latest_row["HE"]

            # スコアの計算
            score_1 = calc_score1(gvm_variance, gvm_slope)
            score_2 = calc_score2(gvm_charge_variance, gvm_charge_slope)
            score_3 = calc_score3(le_he_difference)
            score_4 = calc_score4(probe_current_variance, probe_current_slope)
            score_5 = calc_score5(charge_current_variance, charge_current_slope)

            stability_score = calc_stability_score(score_1, score_2, score_3, score_4, score_5)

            # UTCタイムゾーンを使用
            timestamp = datetime.now(timezone.utc)
            timestamp_proto = _timestamp_pb2.Timestamp()
            timestamp_proto.FromDatetime(timestamp)

            tandem_data = tandem_pb2.TandemData(
                id=str(uuid.uuid4()),
                timestamp=timestamp_proto,
                beam_current_in=latest_row["入射ファラデ電流"]*10,
                beam_current_out=latest_row["加速後の電流"]*10,
                charge_current=latest_row["Charge Current"]*10,
                gvm=str(latest_row["GVM"]/3.9),
                charge_power_supply=latest_row["Charge Power Supply"]*10,
                le=latest_row["LE"]*10,
                he=latest_row["HE"]*10,
                cpo=latest_row["C.P.O"]*10,
                probe_current=latest_row["プローブカレント"]*10,
                probe_position=latest_row["プローブポジション"]*100,
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
                le_he_difference=le_he_difference,
                probe_current_slope=probe_current_slope,
                probe_current_variance=probe_current_variance,
                score_1=score_1,
                score_2=score_2,
                score_3=score_3,
                score_4=score_4,
                score_5=score_5,
                stability_score=stability_score
            )

            print("\n=== タンデム加速器データ ===")
            print(f"時刻: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print("\n【基本測定値】")
            print(f"入射FC電流: {tandem_data.beam_current_in:.3f} [nA]")
            print(f"加速後の電流0度: {tandem_data.beam_current_out:.6f} [μA]")
            print(f"チャージング電流: {tandem_data.charge_current:.3f} [μA]")
            print(f"ターミナル電圧GVM: {float(tandem_data.gvm):.3f} [MV]")
            print(f"チャージングCPS: {tandem_data.charge_power_supply:.3f} [kV]")
            print(f"LE: {tandem_data.le:.3f} [μA]")
            print(f"HE: {tandem_data.he:.3f} [μA]")
            print(f"C.P.O: {tandem_data.cpo:.5f} [V]")
            print(f"プローブ電流: {tandem_data.probe_current:.3f} [μA]")
            print(f"プローブ位置: {tandem_data.probe_position:.3f} [mm]")

            print("\n【計算指標】")
            print(f"透過率: {tandem_data.transmission_ratio:.3f}")
            print(f"透過率の傾き: {transmission_slope:.6f}")
            print(f"透過率の分散: {transmission_variance:.6f}")
            print(f"ビーム損失比: {tandem_data.beam_loss_ratio:.3f}")
            print(f"GVM-チャージ電源の傾き: {gvm_charge_slope:.6f}")
            print(f"GVM-チャージ電源の分散: {gvm_charge_variance:.6f}")
            print(f"GVM-チャージ電源の相関: {gvm_charge_correlation:.3f}")
            print(f"チャージ電流の傾き: {charge_current_slope:.6f}")
            print(f"チャージ電流の分散: {charge_current_variance:.6f}")
            print(f"GVMの傾き: {gvm_slope:.6f}")
            print(f"GVMの分散: {gvm_variance:.6f}")
            print(f"LE-HE差: {le_he_difference:.3f}")
            print(f"プローブ電流の傾き: {probe_current_slope:.6f}")
            print(f"プローブ電流の分散: {probe_current_variance:.6f}")
            print(f"スコア1: {score_1:.3f} (GVMの安定性評価: 分散と傾きの合計)")
            print(f"スコア2: {score_2:.3f} (GVMとCPSの関係性評価: 分散と傾きの合計)")
            print(f"スコア3: {score_3:.3f} (LE-HE差の評価)")
            print(f"スコア4: {score_4:.3f} (プローブカレントの安定性評価: 分散と傾きの合計)")
            print(f"スコア5: {score_5:.3f} (チャージカレントの安定性評価: 分散と傾きの合計)")
            print(f"安定性スコア: {stability_score:.3f} (全スコアの合計、最大100点)")
            print("=" * 30)

            # Supabase送信（同じtimestampが登録済みならスキップ）
            if supabase is not None:
                try:
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
                            "le_he_difference": tandem_data.le_he_difference,
                            "probe_current_slope": tandem_data.probe_current_slope,
                            "probe_current_variance": tandem_data.probe_current_variance,
                            "score_1": tandem_data.score_1,
                            "score_2": tandem_data.score_2,
                            "score_3": tandem_data.score_3,
                            "score_4": tandem_data.score_4,
                            "score_5": tandem_data.score_5,
                            "stability_score": tandem_data.stability_score
                        }).execute()
                    else:
                        print("⚠️ Supabase: 同じtimestampのデータが既に存在するためスキップされました。")
                except Exception as e:
                    print(f"Supabaseデータ保存エラー: {e}")
                    print("データベースへの保存をスキップします。")
            else:
                print("⚠️ Supabase: 接続が確立されていないため、データベースへの保存はスキップされます。")

            yield tandem_data
            await asyncio.sleep(1)

        except Exception as e:
            print(f"データ生成エラー: {e}")
            import traceback
            print("スタックトレース:")
            traceback.print_exc()
            await asyncio.sleep(1)
            continue

async def send_to_grpc():
    credentials = grpc.ssl_channel_credentials()
    while True:  # 永続的な接続を維持
        try:
            async with grpc.aio.secure_channel(
                grpc_address,
                credentials
            ) as channel:
                stub = tandem_pb2_grpc.TandemServiceStub(channel)
                print("gRPC接続を開始します")
                
                try:
                    # イテレータを使ってストリーミング送信
                    response = await stub.SendData(generate_tandem_data())
                    print(f"サーバーからのレスポンス: {response}")
                except Exception as e:
                    print(f"ストリーミングエラー: {e}")
                    continue
                
        except Exception as e:
            print(f"gRPC接続エラー: {e}")
            print("5秒後に再接続を試みます...")
            await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(send_to_grpc())
