"""Small Cache-Aside application used only for the Redis lab."""
import os
import time
from flask import Flask, Response, g, jsonify, request
import redis
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest

app = Flask(__name__)
client = redis.Redis(
    host=os.environ.get('REDIS_SERVICE_HOST') or os.environ.get('REDIS_HOST', 'redis'), port=6379,
    socket_connect_timeout=1, socket_timeout=1, decode_responses=True,
)
ttl = int(os.environ.get('CACHE_TTL', '30'))
hits = Counter('cache_hits_total', 'Cache hits')
misses = Counter('cache_misses_total', 'Cache misses')
source_requests = Counter('source_requests_total', 'Requests to slow source')
http_requests = Counter('app_http_requests_total', 'HTTP requests', ['mode', 'status'])
duration = Histogram('app_http_request_duration_seconds', 'HTTP request time', ['mode'])


@app.before_request
def begin():
    if request.path.startswith('/data/'):
        g.started = time.perf_counter()
        g.mode = request.args.get('cache', 'off')


@app.after_request
def observe(response):
    if hasattr(g, 'started'):
        http_requests.labels(g.mode, str(response.status_code)).inc()
        duration.labels(g.mode).observe(time.perf_counter() - g.started)
    return response


def read_source(item_id):
    source_requests.inc()
    time.sleep(0.05)
    return f'item-{item_id}'


@app.get('/data/<int:item_id>')
def data(item_id):
    mode = g.mode
    if mode not in ('on', 'off'):
        return jsonify(error='cache must be on or off'), 400
    if mode == 'off':
        return jsonify(id=item_id, value=read_source(item_id), cache='off')
    key = f'product:{item_id}'
    try:
        value = client.get(key)
        if value is not None:
            hits.inc()
            return jsonify(id=item_id, value=value, cache='hit')
        misses.inc()
        value = read_source(item_id)
        client.set(key, value, ex=ttl)
        return jsonify(id=item_id, value=value, cache='miss')
    except redis.RedisError:
        return jsonify(error='Redis unavailable'), 503


@app.get('/health')
def health():
    return jsonify(status='ok')


@app.get('/metrics')
def metrics():
    return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, threaded=True)
