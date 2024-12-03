import socket
import time
import requests
import sqlite3
from datetime import datetime

# 設定伺服器參數
HOST = '0.0.0.0'
PORT = 8080

# 摩斯密碼處理相關參數
BUTTON_PRESSED = False
PRESS_TIME = None
RELEASE_TIME = None
MORSE_BUFFER = []
MAX_MORSE_LENGTH = 6

morse_dict = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E",
    "..-.": "F", "--.": "G", "....": "H", "..": "I", ".---": "J",
    "-.-": "K", ".-..": "L", "--": "M", "-.": "N", "---": "O",
    ".--.": "P", "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
    "..-": "U", "...-": "V", ".--": "W", "-..-": "X", "-.--": "Y",
    "--..": "Z",
    "-----": "0", ".----": "1", "..---": "2", "...--": "3", "....-": "4",
    ".....": "5", "-....": "6", "--...": "7", "---..": "8", "----.": "9"
}

def get_db_connection():
    conn = sqlite3.connect('temperature.db')  # 連接到 SQLite 資料庫，若不存在會自動創建
    conn.row_factory = sqlite3.Row       # 設定可以用字典方式訪問結果
    return conn

def save_temperature_to_db(temperature):
    with get_db_connection() as conn:
        conn.execute(
            'INSERT INTO data (time, temperature) VALUES (?, ?)',
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), temperature)
        )
        conn.commit()


def clear_morse():
    """清空摩斯密碼緩衝區"""
    global MORSE_BUFFER
    MORSE_BUFFER = []

def parse_morse_code(morse_buffer):
    """解析摩斯密碼"""
    morse_str = ''.join(morse_buffer)
    
    return morse_dict.get(morse_str, 'Invalid Morse code sequence.')

def is_current_morse_code_possiable(morse_buffer):
    morse_str = ''.join(morse_buffer)
    possible_keys = [key for key in morse_dict.keys() if key.startswith(morse_str)]

    return len(possible_keys) == 0

def handle_button_event(state):
    """處理按鈕事件"""
    global BUTTON_PRESSED, PRESS_TIME, RELEASE_TIME, MORSE_BUFFER

    if state == '1' and not BUTTON_PRESSED:  # 按鈕被按下
        BUTTON_PRESSED = True
        PRESS_TIME = time.time()
    elif state == '0' and BUTTON_PRESSED:  # 按鈕被釋放
        BUTTON_PRESSED = False
        RELEASE_TIME = time.time()

        # 計算按下的持續時間
        duration = (RELEASE_TIME - PRESS_TIME) * 1000  # 轉換為毫秒
        if duration < 200:
            MORSE_BUFFER.append('.')
        else:
            MORSE_BUFFER.append('-')
            
        if len(MORSE_BUFFER) < 5:
            if is_current_morse_code_possiable(MORSE_BUFFER) == 'Invalid Morse code sequence.':
                check_morse_idle(True)
            else:
                payload = {'morse_code': ''.join(MORSE_BUFFER), 'morse_decode': 'Loading...', 'create_new_row': len(MORSE_BUFFER) == 1}
                response = requests.post('http://localhost:5000/morse', json=payload)
                response.raise_for_status()
        else:
            check_morse_idle(True)

def check_morse_idle(force=False):
    """檢查是否有長時間無輸入並處理摩斯密碼"""
    global RELEASE_TIME, BUTTON_PRESSED, MORSE_BUFFER

    if force or RELEASE_TIME:
        idle_duration = (time.time() - RELEASE_TIME) * 1000
        if force or (not BUTTON_PRESSED and idle_duration > 500 and MORSE_BUFFER):
            result = parse_morse_code(MORSE_BUFFER)
            payload = {'morse_code': ''.join(MORSE_BUFFER), 'morse_decode': result, 'create_new_row': False}
            try:
                response = requests.post('http://localhost:5000/morse', json=payload)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Failed to send POST request: {e}")
            clear_morse()


def start_server():
    """啟動Socket伺服器（非阻塞模式）"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 允許地址重用
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        print(f"Server listening on {HOST}:{PORT}...")

        while True:  # 主循環，允許伺服器在客戶端斷線後重新等待
            print("Waiting for a new connection...")
            conn, addr = server_socket.accept()
            conn.setblocking(False)  # 設定為非阻塞模式
            print(f"Connection established with {addr}.")

            try:
                while True:  # 客戶端連接處理循環
                    try:
                        data = conn.recv(2)
                        if not data:  # 檢查連接是否已關閉
                            print("Connection closed by client.")
                            break

                        state = data.decode().strip().rstrip('\x00')  # 去除尾部多餘字元
                        if state in {'0', '1'}:
                            handle_button_event(state)  # 處理按鈕事件
                        else:
                            print(f"Unexpected data received: {state}")
                    except BlockingIOError:
                        # 如果沒有資料可讀，這裡不阻塞，繼續執行其他操作
                        check_morse_idle()  # 檢查摩斯密碼的閒置時間處理
                        time.sleep(0.1)  # 避免無限快速循環浪費CPU
                    except Exception as e:
                        print(f"An error occurred while handling client: {e}")
                        break
            except KeyboardInterrupt:
                print("\nServer shutting down.")
                break
            except Exception as e:
                print(f"An error occurred in the connection loop: {e}")
            finally:
                conn.close()  # 確保連接被正確關閉


def main():
    try:
        start_server()
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
