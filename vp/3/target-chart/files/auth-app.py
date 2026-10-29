import os
import jwt
import datetime
from time import perf_counter
import psycopg2
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, g, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

REQUESTS = Counter('http_requests', 'HTTP requests', ['method', 'route', 'status'])
DURATION = Histogram('http_request_duration_seconds', 'HTTP response time', ['route'])
ERRORS = Counter('http_errors', 'HTTP error responses', ['group'])
ERRORS.labels('4xx')
ERRORS.labels('5xx')

@app.before_request
def start_timer():
    if request.path not in ('/metrics', '/health'):
        g.start_time = perf_counter()

@app.after_request
def record_request(response):
    if hasattr(g, 'start_time'):
        route = request.endpoint or 'unknown'
        REQUESTS.labels(request.method, route, str(response.status_code)).inc()
        DURATION.labels(route).observe(perf_counter() - g.start_time)
        if response.status_code >= 400:
            ERRORS.labels(f'{response.status_code // 100}xx').inc()
    return response

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret-key')
DB_HOST = os.environ.get('DB_HOST', 'postgres')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'users')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password123')
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

LOGIN_TITLE = os.environ.get('LOGIN_TITLE', 'Вход в систему')
WELCOME_TEXT = os.environ.get('WELCOME_TEXT', 'Добро пожаловать!')
PROFILE_SERVICE_URL = os.environ.get('PROFILE_SERVICE_URL', 'http://profile-service:5001')

LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f0f2f5; }
        .login-box { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        input { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background: #45a049; }
        .error { color: red; text-align: center; }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>{{ title }}</h1>
        {% if error %}
        <p class="error">{{ error }}</p>
        {% endif %}
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Логин" required>
            <input type="password" name="password" placeholder="Пароль" required>
            <button type="submit">Войти</button>
        </form>
    </div>
</body>
</html>
'''

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/')
def index():
    return render_template_string(LOGIN_PAGE, title=LOGIN_TITLE, error=None)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, username, password FROM users WHERE username = %s', (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and user[2] == password:
        token = jwt.encode({
            'user_id': user[0],
            'username': user[1],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, JWT_SECRET, algorithm='HS256')

        return jsonify({
            'token': token,
            'message': WELCOME_TEXT,
            'profile_url': PROFILE_SERVICE_URL
        })

    return render_template_string(LOGIN_PAGE, title=LOGIN_TITLE, error='Неверный логин или пароль'), 401

@app.route('/api/auth', methods=['POST'])
def api_auth():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, username, password FROM users WHERE username = %s', (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and user[2] == password:
        token = jwt.encode({
            'user_id': user[0],
            'username': user[1],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, JWT_SECRET, algorithm='HS256')

        return jsonify({'token': token})

    return jsonify({'error': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
