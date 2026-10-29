"""Run the same real k6/Prometheus experiment at 1, 2 and 3 replicas."""

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

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results'
OUT.mkdir(exist_ok=True)
PROM = os.environ.get('PROMETHEUS_URL', 'http://127.0.0.1:9090')
TARGET = os.environ.get('TARGET_URL', 'http://127.0.0.1:30083/work?iterations=20000')
LEVELS = [int(x) for x in os.environ.get('LEVELS', '10,25,50,100').split(',')]
DURATION = int(os.environ.get('DURATION_SECONDS', '60'))
REPLICAS = [int(x) for x in os.environ.get('REPLICAS', '1,2,3').split(',')]
ENV = os.environ.copy()
ENV['KUBECONFIG'] = str(Path.home() / '.kube/config')

QUERIES = {
    'rps': 'sum(rate(http_requests_total{namespace="vp-lr4",route="work"}[30s]))',
    'errors': 'sum(rate(http_requests_total{namespace="vp-lr4",route="work",status=~"[45].."}[30s])) or vector(0)',
    'cpu': 'sum(rate(container_cpu_usage_seconds_total{namespace="vp-lr4",container="auth-service"}[30s]))',
    'memory': 'sum(container_memory_working_set_bytes{namespace="vp-lr4",container="auth-service"}) / 1024 / 1024',
    'server_p95': 'histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{namespace="vp-lr4",route="work"}[30s])))',
    'pod_rps': 'sum by (pod) (rate(work_requests_total{namespace="vp-lr4"}[30s]))',
    'pod_cpu': 'sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="vp-lr4",container="auth-service"}[30s]))',
    'available': 'kube_deployment_status_replicas_available{namespace="vp-lr4",deployment="auth-service"}',
}


def kubectl(*args):
    return subprocess.check_output(['k3s', 'kubectl', '-n', 'vp-lr4', *args],
                                   env=ENV, text=True).strip()


def query_range(expr, begin, end):
    url = PROM + '/api/v1/query_range?' + urlencode({
        'query': expr, 'start': begin, 'end': end, 'step': 5,
    })
    with urlopen(url, timeout=30) as response:
        data = json.load(response)
    if data['status'] != 'success':
        raise RuntimeError(data)
    return data


def samples(data):
    return [float(v) for series in data['data']['result']
            for _, v in series.get('values', []) if math.isfinite(float(v))]


summary_file = OUT / 'summary.json'
old_summary = json.loads(summary_file.read_text()) if summary_file.exists() else {}
rows = old_summary.get('rows', [])
for previous in rows:
    previous.setdefault('target_url', old_summary.get('target_url'))
for replicas in REPLICAS:
    print(f'Scaling to {replicas} replicas', flush=True)
    kubectl('scale', 'deployment/auth-service', f'--replicas={replicas}')
    kubectl('rollout', 'status', 'deployment/auth-service', '--timeout=300s')
    time.sleep(20)
    pod_snapshot = kubectl('get', 'pods', '-l', 'app=auth-service', '-o', 'wide')
    (OUT / f'r{replicas}-pods.txt').write_text(pod_snapshot + '\n')
    for rate in LEVELS:
        if any(r['replicas'] == replicas and r['target_rps'] == rate for r in rows):
            print(f'SKIP replicas={replicas} rate={rate}', flush=True)
            continue
        name = f'r{replicas}-rate{rate}'
        print(f'START {name}', flush=True)
        env = ENV.copy()
        env.update(RATE=str(rate), DURATION=f'{DURATION}s', TARGET_URL=TARGET)
        start = time.time()
        with (OUT / f'{name}.txt').open('w') as output:
            process = subprocess.run(['k6', 'run', '--summary-export',
                                      str(OUT / f'{name}.json'), 'test-scaling.js'],
                                     cwd=ROOT, env=env, stdout=output,
                                     stderr=subprocess.STDOUT)
        end = time.time()
        if not (OUT / f'{name}.json').exists():
            raise RuntimeError(f'k6 did not export {name}; exit={process.returncode}')
        time.sleep(7)
        responses = {key: query_range(expr, end - 30, end) for key, expr in QUERIES.items()}
        (OUT / f'{name}.prometheus.json').write_text(json.dumps({
            'start_utc': datetime.fromtimestamp(start, timezone.utc).isoformat(),
            'end_utc': datetime.fromtimestamp(end, timezone.utc).isoformat(),
            'queries': QUERIES, 'responses': responses,
        }, ensure_ascii=False, indent=2) + '\n')
        metrics = json.loads((OUT / f'{name}.json').read_text())['metrics']
        avg = {key: statistics.mean(samples(value)) if samples(value) else None
               for key, value in responses.items()}
        row = {
            'replicas': replicas, 'target_rps': rate,
            'target_url': TARGET,
            'actual_rps': metrics['http_reqs']['rate'],
            'p95_ms': metrics['http_req_duration']['p(95)'],
            'errors_percent': 100 * metrics['http_req_failed']['value'],
            'dropped_iterations': metrics.get('dropped_iterations', {}).get('count', 0),
            'checks_failed': metrics.get('checks', {}).get('fails', 0),
            'k6_exit': process.returncode,
            'prometheus_rps': avg['rps'],
            'prometheus_cpu_cores': avg['cpu'],
            'prometheus_memory_mib': avg['memory'],
            'prometheus_server_p95_ms': avg['server_p95'] * 1000 if avg['server_p95'] is not None else None,
            'prometheus_available_replicas': avg['available'],
            'start_utc': datetime.fromtimestamp(start, timezone.utc).isoformat(),
            'end_utc': datetime.fromtimestamp(end, timezone.utc).isoformat(),
        }
        rows.append(row)
        summary_file.write_text(json.dumps({'duration_seconds': DURATION,
                                            'rows': rows}, ensure_ascii=False, indent=2) + '\n')
        print(f"DONE {name}: RPS={row['actual_rps']:.2f}, p95={row['p95_ms']:.1f}ms, "
              f"errors={row['errors_percent']:.2f}%, dropped={row['dropped_iterations']}", flush=True)
        time.sleep(15)
