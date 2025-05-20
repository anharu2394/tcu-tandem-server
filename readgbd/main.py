import struct
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# フォント設定（日本語対応）
try:
    font_path = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
    if os.path.exists(font_path):
        plt.rcParams["font.family"] = fm.FontProperties(fname=font_path).get_name()
    else:
        print("⚠️ 日本語フォントが見つかりません。デフォルトフォントを使用します。")
except Exception as e:
    print(f"⚠️ フォント設定に失敗しました: {e}")

# === バイナリ読み取り（CH1〜CH10強制、Alarmは無視） ===
def read_all_analog_channels(file_path):
    header_size = 9216
    record_size = 12 * 2  # 12ch × 2byte

    with open(file_path, "rb") as f:
        f.seek(0, 2)
        file_size = f.tell()
        num_records = (file_size - header_size) // record_size
        f.seek(header_size)
        data_bytes = f.read(num_records * record_size)

    raw_data = np.frombuffer(data_bytes, dtype='>i2')
    data = raw_data.reshape((num_records, 12))
    analog_data_raw = data[:, :10]
    analog_data = analog_data_raw / 200.0  # CH1〜CH10

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
    df = pd.DataFrame(analog_data, columns=channel_names)  # 電圧に変換済み
    df.insert(0, "Time(s)", time)
    return df, channel_names

# === 各チャネルごとに別々のグラフを保存（点のみ） ===
def plot_data(df, channels):
    # 全チャネルまとめてプロット
    plt.figure(figsize=(12, 6))
    for ch in channels:
        plt.plot(df["Time(s)"], df[ch], label=ch)
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")
    plt.title("All Channels (CH1–CH10)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("outputs/all_channels_plot.png")
    plt.close()
    print(f"📦 channels: {channels}")
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    for ch in channels:
        plt.figure(figsize=(10, 4))
        plt.scatter(df["Time(s)"], df[ch], s=2)
        plt.xlabel("Time (s)")
        plt.ylabel("Voltage (V)")
        plt.title(f"{ch} Time Series (Scatter Plot)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"{ch}_plot.png"))
        plt.close()

    df.to_csv(os.path.join(output_dir, "analog_channels_data.csv"), index=False)
    print("✅ アナログチャネルのグラフとCSVを保存しました: outputs/")

# === 実行 ===
FILE_PATH = "../gbd/GL240 01 Mar 26 2025.gbd"
if __name__ == "__main__":
    df, channels = read_all_analog_channels(FILE_PATH)
    plot_data(df, channels)
