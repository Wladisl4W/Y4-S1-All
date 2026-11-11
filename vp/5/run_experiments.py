"""Real k6 experiments; save each original result and exact run parameters."""
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results'
OUT.mkdir(exist_ok=True)
ENV = os.environ | {'KUBECONFIG': str(Path.home() / '.kube/config')}
TARGET = os.environ['TARGET_URL'].rstrip('/')
SUMMARY = OUT / 'summary.json'
rows = json.loads(SUMMARY.read_text())['rows'] if SUMMARY.exists() else []


def kubectl(*args):
    return subprocess.check_output(['k3s', 'kubectl', '-n', 'vp-lr5', *args],
                                   env=ENV, text=True).strip()


COUNTERS = ('cache_hits_total', 'cache_misses_total', 'source_requests_total')


def metrics_snapshot():
    # An overloaded single worker may need time to drain its queue after k6.
    deadline = time.monotonic() + 240
    while True:
        try:
            body = urlopen(f'{TARGET}/metrics', timeout=10).read().decode()
            return {name: float(match.group(1)) if (match := re.search(
                r'^' + re.escape(name) + r' ([0-9.]+)$', body, re.M)) else 0.0
                for name in COUNTERS}
        except OSError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(5)


def prometheus(name, query, start, end):
    pod = subprocess.check_output([
        'k3s', 'kubectl', '-n', 'monitoring', 'get', 'pod',
        'prometheus-prometheus-kube-prometheus-prometheus-0',
        '-o', 'jsonpath={.status.podIP}'], env=ENV, text=True).strip()
    url = f'http://{pod}:9090/api/v1/query_range?' + urlencode({
        'query': query, 'start': start, 'end': end, 'step': 5})
    with urlopen(url, timeout=30) as response:
        result = json.load(response)
    if result['status'] != 'success':
        raise RuntimeError(f'Prometheus {name}: {result}')
    return result


queries = {
    'http_rps': 'sum(rate(app_http_requests_total{namespace="vp-lr5"}[15s]))',
    'hits': 'sum(rate(cache_hits_total{namespace="vp-lr5"}[15s])) or vector(0)',
    'misses': 'sum(rate(cache_misses_total{namespace="vp-lr5"}[15s])) or vector(0)',
    'source_rps': 'sum(rate(source_requests_total{namespace="vp-lr5"}[15s])) or vector(0)',
    'server_p95': 'histogram_quantile(0.95, sum by (le) (rate(app_http_request_duration_seconds_bucket{namespace="vp-lr5"}[15s])))',
}


def run(name, mode, rate, keys, duration, ttl, warm=False):
    if any(r['name'] == name for r in rows):
        print('SKIP', name, flush=True)
        return
    kubectl('set', 'env', 'deployment/cache-app', f'CACHE_TTL={ttl}')
    kubectl('rollout', 'status', 'deployment/cache-app', '--timeout=180s')
    kubectl('exec', 'deployment/redis', '--', 'redis-cli', 'FLUSHDB')
    if warm and mode == 'on':
        for item in range(1, keys + 1):
            urlopen(f'{TARGET}/data/{item}?cache=on', timeout=10).read()
    time.sleep(7)
    before = metrics_snapshot()
    env = ENV | {'MODE': mode, 'RATE': str(rate), 'KEY_COUNT': str(keys),
                 'DURATION': f'{duration}s', 'TARGET_URL': TARGET}
    start = time.time()
    with (OUT / f'{name}.txt').open('w') as output:
        p = subprocess.run(['k6', 'run', '--summary-export', str(OUT / f'{name}.json'),
                            'test-cache.js'], cwd=ROOT, env=env,
                           stdout=output, stderr=subprocess.STDOUT)
    end = time.time()
    after = metrics_snapshot()
    if any(after[m] < before[m] for m in before):
        raise RuntimeError(f'{name}: counters reset during test; result not accepted')
    dbsize = int(kubectl('exec', 'deployment/redis', '--', 'redis-cli', 'DBSIZE').splitlines()[-1])
    response = {key: prometheus(key, expr, start, end)
                for key, expr in queries.items()}
    (OUT / f'{name}.prometheus.json').write_text(json.dumps({
        'queries': queries, 'responses': response,
        'start_utc': datetime.fromtimestamp(start, timezone.utc).isoformat(),
        'end_utc': datetime.fromtimestamp(end, timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2) + '\n')
    metrics = json.loads((OUT / f'{name}.json').read_text())['metrics']
    hits = after['cache_hits_total'] - before['cache_hits_total']
    misses = after['cache_misses_total'] - before['cache_misses_total']
    source = after['source_requests_total'] - before['source_requests_total']
    row = {
        'name': name, 'mode': mode, 'rate': rate, 'keys': keys,
        'duration_seconds': duration, 'ttl_seconds': ttl, 'warm': warm,
        'target_url': TARGET, 'k6_exit': p.returncode,
        'actual_rps': metrics['http_reqs']['rate'],
        'p50_ms': metrics['http_req_duration']['med'],
        'p95_ms': metrics['http_req_duration']['p(95)'],
        'p99_ms': metrics['http_req_duration']['p(99)'],
        'errors_percent': metrics['http_req_failed']['value'] * 100,
        'dropped_iterations': metrics.get('dropped_iterations', {}).get('count', 0),
        'hits': hits, 'misses': misses, 'hit_ratio_percent': 100 * hits / (hits + misses) if hits + misses else None,
        'source_requests': source, 'source_rps': source / (end - start),
        'elapsed_seconds': end - start,
        'redis_keys_after': dbsize,
        'start_utc': datetime.fromtimestamp(start, timezone.utc).isoformat(),
        'end_utc': datetime.fromtimestamp(end, timezone.utc).isoformat(),
    }
    if name.startswith(('keys-', 'ttl-')) and (
        row['elapsed_seconds'] > duration + 30 or
        row['actual_rps'] < rate * 0.95 or
        row['errors_percent'] >= 1 or
        row['dropped_iterations'] != 0
    ):
        raise RuntimeError(f'{name}: fixed-rate experiment did not meet run validity checks; result not accepted')
    rows.append(row)
    SUMMARY.write_text(json.dumps({'rows': rows}, ensure_ascii=False, indent=2) + '\n')
    print('DONE', name, f"RPS={row['actual_rps']:.2f}",
          f"p95={row['p95_ms']:.0f}ms", f"errors={row['errors_percent']:.2f}%",
          f"hits={row['hit_ratio_percent']}", flush=True)
    time.sleep(8)


if __name__ == '__main__':
    for rate in (10, 25, 50, 100, 200, 400):
        run(f'off-r{rate}', 'off', rate, 10, 60, 30)
        run(f'on-r{rate}', 'on', rate, 10, 60, 30, warm=True)
    for keys in (10, 100, 1000):
        # At 10 RPS, 1000 objects require at least 100 seconds to be requested.
        run(f'keys-{keys}', 'on', 10, keys, 120 if keys == 1000 else 60, 30)
    for ttl in (5, 30, 120):
        run(f'ttl-{ttl}', 'on', 10, 10, 150, ttl)
