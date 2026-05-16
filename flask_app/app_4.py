import base64
from flask import Flask, render_template, request, redirect, url_for, session
from flask_caching import Cache
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import redis
from pymongo import MongoClient
from config import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

REDIS_URL = f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/0"
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_REDIS'] = redis.from_url(REDIS_URL)
Session(app)

app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_URL'] = REDIS_URL
app.config['CACHE_DEFAULT_TIMEOUT'] = 60
cache = Cache(app)

mongo_client = MongoClient(Config.MONGODB_URL)
db = mongo_client[Config.MONGODB_CATALOG_DB]
users_collection = db["users"]

def create_admin():
    admin = users_collection.find_one({"login": Config.ADMIN_USERNAME})
    if not admin:
        users_collection.insert_one({
            "login": Config.ADMIN_USERNAME,
            "password_hash": generate_password_hash(Config.ADMIN_PASSWORD),
            "name": "Администратор",
            "is_admin": True,
            "avatar_base64": None,
            "avatar_mime": "image/jpeg"
        })
        print(f"Админ создан: {Config.ADMIN_USERNAME} / {Config.ADMIN_PASSWORD}")

create_admin()

@app.route('/', methods=['GET', 'POST'])
def auth():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    error = None
    success = None
    if request.method == 'POST':
        action = request.form.get('action')
        login = request.form.get('login')
        password = request.form.get('password')
        user = users_collection.find_one({"login": login})
        if action == "register":
            if user:
                error = "Такой логин уже занят"
            else:
                users_collection.insert_one({
                    "login": login,
                    "password_hash": generate_password_hash(password),
                    "name": "Пользователь",
                    "is_admin": False,
                    "avatar_base64": None,
                    "avatar_mime": "image/jpeg"
                })
                success = "Регистрация успешна. Теперь войдите"
        elif action == "login":
            if user and check_password_hash(user["password_hash"], password):
                session['user'] = login
                session['is_admin'] = user.get('is_admin', False)
                return redirect(url_for('dashboard'))
            error = "Неверный логин или пароль"
    return render_template('auth.html', error=error, success=success)

@app.route('/dashboard')
@cache.cached(timeout=30)
def dashboard():
    if 'user' not in session:
        return redirect(url_for('auth'))
    return render_template('dashboard.html', username=session['user'], is_admin=session.get('is_admin', False))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('auth'))
    user = users_collection.find_one({"login": session['user']})
    if request.method == 'POST':
        name = request.form.get('name')
        users_collection.update_one(
            {"login": session['user']},
            {"$set": {"name": name}}
        )
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file.filename:
                avatar_base64 = base64.b64encode(file.read()).decode('utf-8')
                users_collection.update_one(
                    {"login": session['user']},
                    {"$set": {
                        "avatar_base64": avatar_base64,
                        "avatar_mime": file.content_type or "image/jpeg"
                    }}
                )
        cache.delete_memoized(dashboard)
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)

@app.route('/admin')
def admin_panel():
    if 'user' not in session or not session.get('is_admin', False):
        return redirect(url_for('auth'))
    users = list(users_collection.find({}, {"password_hash": 0}))
    stats = {
        "total_users": users_collection.count_documents({}),
        "admins": users_collection.count_documents({"is_admin": True}),
        "regular_users": users_collection.count_documents({"is_admin": {"$ne": True}}),
        "users_with_avatar": users_collection.count_documents({"avatar_base64": {"$ne": None}})
    }
    return render_template('admin.html', users=users, stats=stats)

@app.route('/logout')
def logout():
    session.clear()
    cache.clear()
    return redirect(url_for('auth'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)