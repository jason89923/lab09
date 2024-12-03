from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit
import time
from datetime import datetime
import sqlite3

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

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

# 最近更新的時間
last_update_time = None

@app.route('/get_temperature', methods=['POST'])
def get_temperature_data():
    global last_update_time
    try:
        temperature = request.get_json().get('temperature')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 當前時間



        # 更新最近的資料庫更新時間
        last_update_time = timestamp

        # 廣播最新溫度和資料庫內容給所有客戶端
        socketio.emit('temperature_update', {"temperature": temperature})

        # 查詢最新的 10 筆數據
        cursor.execute('SELECT time, temperature FROM temperature_table ORDER BY id DESC LIMIT 10')
        data = cursor.fetchall()

        # 格式化數據為字典
        formatted_data = [{"time": row[0], "temperature": row[1]} for row in data]

        socketio.emit('database_update', {
            "last_update_time": last_update_time,
            "data": formatted_data
        })

        return jsonify({"message": "Temperature data updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Error updating temperature data: {e}"}), 500

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
    提供資料庫內容的 API，包含最近更新時間
    """
    try:
        # 查詢所有數據
        cursor.execute('SELECT time, temperature FROM temperature_table ORDER BY id DESC')
        data = cursor.fetchall()

        # 格式化數據為字典
        formatted_data = [{"time": row[0], "temperature": row[1]} for row in data]

        return jsonify({
            "last_update_time": last_update_time,
            "data": formatted_data
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
        # 查詢所有數據
        cursor.execute('SELECT time, temperature FROM temperature_table ORDER BY id DESC')
        data = cursor.fetchall()

        # 格式化數據為字典
        formatted_data = [{"time": row[0], "temperature": row[1]} for row in data]
        
        emit('database_update', {
            "last_update_time": last_update_time,
            "data": formatted_data
        })
    except Exception as e:
        print(f"無法發送資料庫內容: {e}")



@app.route('/get-weather-data', methods=['GET'])
def get_weather_data():
    try:
        # 查詢所有數據
        cursor.execute('SELECT date, weekday, weather FROM weather_table ORDER BY id DESC')
        rows = cursor.fetchall()
        
        # 將數據轉換為字典列表
        data = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
        print(data)
        
        return jsonify(data), 200  # 返回數據和 HTTP 200 OK 狀態碼

    except Exception as e:
        print(f"無法發送資料庫內容: {e}")
        return jsonify({"error": "無法取得天氣數據", "details": str(e)}), 500  # 返回錯誤和 HTTP 500 狀態碼





if __name__ == '__main__':
    # 啟動 Flask-SocketIO 伺服器
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
