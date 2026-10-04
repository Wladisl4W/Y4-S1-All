import os
import datetime
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

NOTIFICATION_LOG = os.environ.get('NOTIFICATION_LOG', '/tmp/notifications.log')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'info')
NOTIFICATIONS_TITLE = os.environ.get('NOTIFICATIONS_TITLE', 'Уведомления')

NOTIFICATIONS_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #f0f2f5; padding: 20px; }
        .notifications-box { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; width: 100%; }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .notification-item { padding: 15px; margin: 10px 0; background: #f9f9f9; border-radius: 4px; border-left: 4px solid #4CAF50; }
        .notification-item.welcome { border-left-color: #2196F3; }
        .notification-item.info { border-left-color: #FF9800; }
        .timestamp { color: #999; font-size: 12px; }
        .type { color: #666; font-weight: bold; text-transform: uppercase; font-size: 11px; }
        .message { color: #333; margin-top: 5px; }
        .empty { color: #999; text-align: center; padding: 30px; }
    </style>
</head>
<body>
    <div class="notifications-box">
        <h1>{{ title }}</h1>
        <p style="text-align: center; color: #666;">Пользователь: {{ username }} (ID: {{ user_id }})</p>
        {% if notifications %}
            {% for n in notifications %}
            <div class="notification-item {{ n.type }}">
                <div class="timestamp">{{ n.time }}</div>
                <div class="type">{{ n.type }}</div>
                <div class="message">{{ n.message }}</div>
            </div>
            {% endfor %}
        {% else %}
            <div class="empty">Нет уведомлений</div>
        {% endif %}
    </div>
</body>
</html>
'''

def log_notification(message):
    timestamp = datetime.datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}\n"
    with open(NOTIFICATION_LOG, 'a') as f:
        f.write(log_entry)
    if LOG_LEVEL == 'debug':
        print(log_entry.strip())

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/notify', methods=['POST'])
def notify():
    data = request.get_json()

    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400

    user_id = data.get('user_id', 'unknown')
    message = data['message']
    notification_type = data.get('type', 'info')

    log_notification(f"Notification to user {user_id}: [{notification_type}] {message}")

    return jsonify({
        'status': 'sent',
        'user_id': user_id,
        'type': notification_type,
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/notify/welcome', methods=['POST'])
def notify_welcome():
    data = request.get_json()
    user_id = data.get('user_id', 'unknown')
    username = data.get('username', 'User')

    message = f"Добро пожаловать, {username}!"
    log_notification(f"Welcome notification to user {user_id}: {message}")

    return jsonify({
        'status': 'sent',
        'user_id': user_id,
        'type': 'welcome',
        'message': message,
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/notifications/<int:user_id>')
def get_notifications(user_id):
    notifications = []
    if os.path.exists(NOTIFICATION_LOG):
        with open(NOTIFICATION_LOG, 'r') as f:
            for line in f:
                if f"user {user_id}:" in line or f"user {user_id}:" in line:
                    notifications.append(line.strip())

    return jsonify({
        'user_id': user_id,
        'notifications': notifications
    })

@app.route('/notifications/<int:user_id>')
def notifications_page(user_id):
    notifications = []
    if os.path.exists(NOTIFICATION_LOG):
        with open(NOTIFICATION_LOG, 'r') as f:
            for line in f:
                if f"user {user_id}:" in line:
                    line = line.strip()
                    parts = line.split('] ', 1)
                    if len(parts) == 2:
                        time = parts[0].lstrip('[')
                        rest = parts[1]
                        type_start = rest.find('[')
                        type_end = rest.find(']', type_start) if type_start != -1 else -1
                        if type_start != -1 and type_end != -1:
                            ntype = rest[type_start+1:type_end]
                            message = rest[type_end+2:]
                        else:
                            ntype = 'info'
                            message = rest
                        notifications.append({
                            'time': time,
                            'type': ntype,
                            'message': message
                        })

    return render_template_string(
        NOTIFICATIONS_PAGE,
        title=NOTIFICATIONS_TITLE,
        user_id=user_id,
        username=f"user_{user_id}",
        notifications=notifications
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
