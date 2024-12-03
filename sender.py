import os
import glob
import time
import socket
from datetime import datetime

# 加載模組
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# 設置檔案路徑
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

# 打開檔案並保持文件描述符打開
file_handle = open(device_file, 'r')

def read_temp_raw(handle):
    # 移動到檔案開頭，然後讀取內容
    handle.seek(0)
    lines = handle.readlines()
    return lines

def read_temp(handle):
    lines = read_temp_raw(handle)
    # 確保檢測數據準確
    if lines[0].strip()[-3:] != 'YES':
        return None  # 如果數據無效，返回 None

    # 解析溫度數據
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

def establish_connection():
    # 設置 socket 連接
    server_address = ('127.0.0.1', 8080)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(server_address)
        print("Connected to server at 127.0.0.1:8080")
        return sock
    except ConnectionRefusedError:
        print("Error: Unable to connect to server on 127.0.0.1:8080")
        sock.close()
        raise

try:
    # 啟動時建立與伺服器的連線
    sock = establish_connection()

    # 不斷讀取並傳送溫度
    while True:
        start_time = time.time()  # 記錄開始時間
        temp = read_temp(file_handle)
        if temp is not None:
            print(f"Temperature: {temp:.2f}°C")
            try:
                # 傳送溫度數據
                message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{temp:.2f}"
                sock.sendall(message.encode('utf-8'))
                print(f"Sent: {message}")
            except (socket.error, BrokenPipeError):
                print("Connection lost. Attempting to reconnect...")
                sock.close()
                sock = establish_connection()
        else:
            print("Waiting for valid data...")

        # 確保每次執行間隔為 1 秒
        elapsed_time = time.time() - start_time
        time.sleep(max(1.0 - elapsed_time, 0))  # 如果執行時間超過 1 秒，則不等待
finally:
    # 確保文件描述符和 socket 在程序結束時關閉
    file_handle.close()
    sock.close()
