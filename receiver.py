import socket
import requests
import sqlite3
from datetime import datetime

# 初始化資料庫連線
sql = sqlite3.connect('temperature.db', check_same_thread=False)
cursor = sql.cursor()

# 建立資料表（如果尚未存在）
cursor.execute('''
    CREATE TABLE IF NOT EXISTS temperature_table (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT NOT NULL,
        temperature REAL NOT NULL
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS weather_table (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        weekday REAL NOT NULL,
        weather REAL NOT NULL
    )
''')
sql.commit()


def send_to_http_server(data):
    url = 'http://127.0.0.1:5000/get_temperature'
    try:
        # 發送 POST 請求
        response = requests.post(url, json={'temperature': data})
        if response.status_code == 200:
            print(f"Data successfully posted to {url}")
        else:
            print(f"Failed to post data to {url}. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error posting data to {url}: {e}")

def start_server(host='127.0.0.1', port=8080):
    # 建立 TCP 伺服器
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 允許地址重用
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"Server listening on {host}:{port}")

        while True:
            # 接受客戶端連接
            conn, addr = server_socket.accept()
            with conn:
                print(f"Connection established with {addr}")
                while True:
                    # 接收數據
                    data = conn.recv(1024)  # 每次最多接收 1024 字節
                    if not data:
                        # 如果接收到空數據，結束連接
                        print(f"Connection closed by {addr}")
                        break
                    # 顯示接收到的數據
                    timestamp, received_data = data.decode('utf-8').split(',')
                    print(f"Time: {timestamp}, Received: {received_data}")
                    
                    # 將數據插入 SQLite 資料庫
                    cursor.execute('INSERT INTO temperature_table (time, temperature) VALUES (?, ?)', (timestamp, received_data))
                    sql.commit()
                    
                    # 發送到 HTTP 伺服器
                    send_to_http_server(received_data)

if __name__ == '__main__':
    
    start_server()
