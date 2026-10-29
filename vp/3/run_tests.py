"""Run five real k6 experiments and capture the matching Prometheus series."""

import json
import math
import os
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


folder = Path(__file__).parent
results = folder / 'results'
results.mkdir(exist_ok=True)
prometheus = os.environ.get('PROMETHEUS_URL', 'http://127.0.0.1:9090')
target = os.environ.get('TARGET_URL', 'http://127.0.0.1:30082/')
duration = int(os.environ.get('DURATION_SECONDS', '90'))
levels = tuple(int(value) for value in os.environ.get('LEVELS', '10,25,50,100,200').split(','))

queries = {
    'rps': 'sum(rate(http_requests_total{namespace="vp-lr3",route="index"}[1m]))',
    'errors_5xx': 'sum(rate(http_requests_total{namespace="vp-lr3",status=~"5.."}[1m])) or vector(0)',
    'error_rate_percent': '100 * (sum(rate(http_requests_total{namespace="vp-lr3",status=~"5.."}[1m])) or vector(0)) / clamp_min(sum(rate(http_requests_total{namespace="vp-lr3",route="index"}[1m])), 0.001)',
    'p95_seconds': 'histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{namespace="vp-lr3",route="index"}[1m])))',
    'p99_seconds': 'histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket{namespace="vp-lr3",route="index"}[1m])))',
    'cpu_cores': 'sum(rate(container_cpu_usage_seconds_total{namespace="vp-lr3",container="auth-service"}[1m]))',
    'memory_mib': 'sum(container_memory_working_set_bytes{namespace="vp-lr3",container="auth-service"}) / 1024 / 1024',
}


def api(path, parameters):
    with urlopen(prometheus + path + '?' + urlencode(parameters), timeout=20) as response:
        answer = json.load(response)
    if answer['status'] != 'success':
        raise RuntimeError(answer)
    return answer


def values(answer):
    return [float(point[1])
            for series in answer['data']['result']
            for point in series.get('values', [series.get('value')])
            if point is not None and math.isfinite(float(point[1]))]


if 1 not in values(api('/api/v1/query', {'query': 'up{namespace="vp-lr3",service="auth-service"}'})):
    raise RuntimeError('Prometheus не видит auth-service в vp-lr3')

summary_file = results / 'summary.json'
rows = json.loads(summary_file.read_text())['rows'] if summary_file.exists() else []
for vus in levels:
    if any(row['vus'] == vus for row in rows):
        print(f'SKIP {vus} VU: existing result', flush=True)
        continue
    name = f'vu{vus}'
    print(f'START {vus} VU for {duration}s', flush=True)
    env = os.environ.copy()
    env.update({'VUS': str(vus), 'DURATION': f'{duration}s', 'TARGET_URL': target})
    start = time.time()
    with (results / f'{name}.txt').open('w') as output:
        process = subprocess.run(
            ['k6', 'run', '--summary-export', str(results / f'{name}.json'),
             'test-stages.js'], cwd=folder, env=env, stdout=output,
            stderr=subprocess.STDOUT,
        )
    end = time.time()
    if process.returncode:
        raise RuntimeError(f'k6 failed at {vus} VU: exit {process.returncode}')
    time.sleep(7)
    responses = {key: api('/api/v1/query_range', {
        'query': query, 'start': end - 30, 'end': end, 'step': 5,
    }) for key, query in queries.items()}
    averages = {}
    for key, answer in responses.items():
        numbers = values(answer)
        if not numbers:
            raise RuntimeError(f'Prometheus has no {key} samples for {vus} VU')
        averages[key] = statistics.mean(numbers)
    k6 = json.loads((results / f'{name}.json').read_text())['metrics']
    record = {
        'vus': vus, 'start_utc': datetime.fromtimestamp(start, timezone.utc).isoformat(),
        'end_utc': datetime.fromtimestamp(end, timezone.utc).isoformat(),
        'queries': queries, 'responses': responses, 'averages': averages,
    }
    (results / f'{name}.prometheus.json').write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + '\n'
    )
    row = {
        'vus': vus,
        'rps_k6': k6['http_reqs']['rate'],
        'p95_k6_ms': k6['http_req_duration']['p(95)'],
        'p99_k6_ms': k6['http_req_duration']['p(99)'],
        'errors_k6_percent': k6['http_req_failed']['value'] * 100,
        'rps_grafana': averages['rps'],
        'p95_grafana_ms': averages['p95_seconds'] * 1000,
        'cpu_cores': averages['cpu_cores'],
        'memory_mib': averages['memory_mib'],
        'errors_5xx_per_second': averages['errors_5xx'],
        'error_rate_percent': averages['error_rate_percent'],
        'start_utc': record['start_utc'], 'end_utc': record['end_utc'],
    }
    rows.append(row)
    (results / 'summary.json').write_text(
        json.dumps({'rows': rows}, ensure_ascii=False, indent=2) + '\n'
    )
    print(f"DONE {vus} VU: k6 {row['rps_k6']:.2f} RPS, p95 {row['p95_k6_ms']:.2f} ms; "
          f"Prometheus {row['rps_grafana']:.2f} RPS, p95 {row['p95_grafana_ms']:.2f} ms",
          flush=True)
    if vus != levels[-1]:
        time.sleep(15)
