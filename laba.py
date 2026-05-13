import os
import time
import json
from flask import Flask, session, jsonify, request
from flask_caching import Cache
from flask_session import Session
import redis
from pymongo import MongoClient, ASCENDING, DESCENDING
import gridfs

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key'

MONGO_URI = 'mongodb://localhost:27017/'
REDIS_URL = 'redis://127.0.0.1:6379/0'

# MongoDB setup
mongo_client = MongoClient(MONGO_URI)
db_catalog = mongo_client['Catalog']
pc_components = db_catalog['PC_components']
fs = gridfs.GridFS(mongo_client['AVATARS'])

# Redis setup (Caching & Sessions)
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_URL'] = REDIS_URL
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(REDIS_URL)

cache = Cache(app)
Session(app)

# ЗАДАНИЕ 1
@app.route('/db/init')
def init_db():
    pc_components.delete_many({})  # Очистка
    
    data = []
    # Пример данных для каждой категории (минимум 6 штук на категорию)
    categories_info = [
        ("Материнская плата", {"Socket": "AM4", "Format": "ATX"}),
        ("Процессор", {"Socket": "AM4", "Frequency": "3.8 GHz"}),
        ("ОЗУ", {"Frequency": "3200 MHz", "Capacity": "16GB"}),
        ("ПЗУ", {"Form-Factor": "M.2", "Capacity": "1TB"}),
        ("Видеокарта", {"VRAM": "8GB", "Ports": "HDMI, DP"})
    ]

    for cat_name, params in categories_info:
        for i in range(1, 7):
            doc = {
                "Production": f"Brand_{i}",
                "Model": f"{cat_name} Model {i}",
                "Price": 5000 + (i * 1000),
                "Category": {
                    "Type": cat_name,
                    "Description": f"High-quality {cat_name.lower()}",
                    **params # Распаковка специфичных полей
                }
            }
            # Специальное условие для AM4 (Задание 2)
            if i % 2 == 0: doc["Category"]["Socket"] = "AM4"
            data.append(doc)

    pc_components.insert_many(data)
    return jsonify({"status": "Database initialized with 30 items"})

# ЗАДАНИЕ 2
@app.route('/db/queries')
def run_queries():
    # 1. Самая дешевая/дорогая сборки (по 1 предмету из типа)
    types = ["Материнская плата", "Процессор", "ОЗУ", "ПЗУ", "Видеокарта"]
    cheap_build = []
    expensive_build = []
    
    for t in types:
        cheap_build.append(pc_components.find_one({"Category.Type": t}, sort=[("Price", 1)]))
        expensive_build.append(pc_components.find_one({"Category.Type": t}, sort=[("Price", -1)]))

    # 2. Третий и пятый по стоимости (для примера возьмем Процессоры)
    third_fifth = list(pc_components.find({"Category.Type": "Процессор"}).sort("Price", 1).skip(2).limit(3))
    
    # 3. Сборки на сокете AM4
    am4_boards = list(pc_components.find({"Category.Type": "Материнская плата", "Category.Socket": "AM4"}))
    am4_cpus = list(pc_components.find({"Category.Type": "Процессор", "Category.Socket": "AM4"}))

    return jsonify({
        "cheap_build_sum": sum(item['Price'] for item in cheap_build),
        "expensive_build_sum": sum(item['Price'] for item in expensive_build),
        "third_item": third_fifth[0]['Model'],
        "fifth_item": third_fifth[2]['Model'] if len(third_fifth) > 2 else "None",
        "am4_combinations_count": len(am4_boards) * len(am4_cpus)
    })

# ЗАДАНИЕ 3
@app.route('/avatar/upload', methods=['POST'])
def upload_avatar():
    if 'file' not in request.files: return "No file", 400
    file = request.files['file']
    user_id = request.form.get('user_id')
    file_id = fs.put(file, filename=file.filename, user_id=user_id)
    return jsonify({"file_id": str(file_id)})

# ЗАДАНИЕ 4
@app.route('/api/data')
@cache.cached(timeout=30)
def get_cached_data():
    time.sleep(2) # Имитация нагрузки
    return jsonify({"data": "This is cached for 30s", "time": time.time()})

@app.route('/auth/login')
def login():
    session['user'] = 'student_name'
    return "Logged in and session saved to Redis"

@app.route('/auth/me')
def me():
    user = session.get('user', 'Guest')
    return f"Hello, {user}. Session is loaded from Redis."

if __name__ == '__main__':
    app.run(debug=True)