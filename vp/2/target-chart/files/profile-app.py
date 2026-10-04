import os
import jwt
import psycopg2
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret-key')
DB_HOST = os.environ.get('DB_HOST', 'postgres')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'users')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password123')
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

PROFILE_TITLE = os.environ.get('PROFILE_TITLE', 'Профиль пользователя')
NOTIFICATION_SERVICE_URL = os.environ.get('NOTIFICATION_SERVICE_URL', 'http://notification-service:5002')

PROFILE_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f0f2f5; }
        .profile-box { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .info { margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 4px; }
        .label { font-weight: bold; color: #666; }
    </style>
</head>
<body>
    <div class="profile-box">
        <h1>{{ title }}</h1>
        <div class="info">
            <span class="label">ID:</span> {{ user_id }}
        </div>
        <div class="info">
            <span class="label">Логин:</span> {{ username }}
        </div>
        <div class="info">
            <span class="label">Email:</span> {{ email }}
        </div>
        <div class="info">
            <span class="label">Дата регистрации:</span> {{ created_at }}
        </div>
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

@app.route('/api/profile')
def api_profile():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token required'}), 401

    token = auth_header.split(' ')[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload['user_id']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, username, email, created_at FROM users WHERE id = %s', (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            return jsonify({
                'user_id': user[0],
                'username': user[1],
                'email': user[2],
                'created_at': str(user[3])
            })

        return jsonify({'error': 'User not found'}), 404

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

@app.route('/profile/<token>')
def profile_page(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload['user_id']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, username, email, created_at FROM users WHERE id = %s', (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            return render_template_string(
                PROFILE_PAGE,
                title=PROFILE_TITLE,
                user_id=user[0],
                username=user[1],
                email=user[2],
                created_at=user[3]
            )

        return jsonify({'error': 'User not found'}), 404

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
