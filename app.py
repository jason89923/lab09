from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO, emit
import threading
import time
import random
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 模擬的資料庫（使用列表代替真正的資料庫）
mock_database = []

# 最近更新的時間
last_update_time = None

# 模擬生成即時溫度數據
def generate_temperature_data():
    global last_update_time
    while True:
        try:
            # 隨機生成溫度
            temperature = round(random.uniform(20.0, 30.0), 1)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 當前時間

            # 添加到模擬資料庫
            mock_database.append({"timestamp": timestamp, "temperature": temperature})

            # 保留最近 10 筆數據
            if len(mock_database) > 10:
                mock_database.pop(0)

            # 更新最近的資料庫更新時間
            last_update_time = timestamp

            # 廣播最新溫度和資料庫內容給所有客戶端
            socketio.emit('temperature_update', {"temperature": temperature})
            socketio.emit('database_update', {
                "last_update_time": last_update_time,
                "data": mock_database
            })

            time.sleep(1)  # 模擬數據生成間隔
        except Exception as e:
            print(f"資料生成錯誤: {e}")

@app.route('/')
def index():
    """
    返回前端頁面
    """
    return render_template('temperature.html')

@app.route('/weather')
def weather():
    """
    返回 weather.html 頁面
    """
    return render_template('weather.html')

@app.route('/get-database-content', methods=['GET'])
def get_database_content():
    """
    提供模擬資料庫內容的 API，包含最近更新時間
    """
    try:
        return jsonify({
            "last_update_time": last_update_time,
            "data": mock_database
        })
    except Exception as e:
        return jsonify({"error": f"無法取得資料庫內容: {e}"}), 500

@socketio.on('connect')
def handle_connect():
    """
    處理客戶端連接事件
    """
    print("客戶端已連接")
    try:
        emit('database_update', {
            "last_update_time": last_update_time,
            "data": mock_database
        })
    except Exception as e:
        print(f"無法發送資料庫內容: {e}")
        
 # 假設的天氣數據
weather_data = [
    {"date": "2024-12-02", "weekday": "星期一", "weather": "晴"},
    {"date": "2024-12-03", "weekday": "星期二", "weather": "多雲"},
    {"date": "2024-12-04", "weekday": "星期三", "weather": "小雨"}
]

@app.route('/get-weather-data', methods=['GET'])
def get_weather_data():
    return jsonify(weather_data)       
        

if __name__ == '__main__':
    # 啟動模擬數據生成執行緒
    threading.Thread(target=generate_temperature_data, daemon=True).start()

    # 啟動 Flask-SocketIO 伺服器
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
