import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


folder = Path(__file__).parent
metrics = [
    'container_cpu_usage_seconds_total{namespace="vp-lr2",container="auth-service"}',
    'process_cpu_seconds_total{namespace="vp-lr2",service="auth-service"}',
    'container_memory_working_set_bytes{namespace="vp-lr2",container="auth-service"}',
    'process_resident_memory_bytes{namespace="vp-lr2",service="auth-service"}',
    'http_requests_total{namespace="vp-lr2",service="auth-service"}',
    'http_request_duration_seconds_bucket{namespace="vp-lr2",service="auth-service"}',
    'http_errors_total{namespace="vp-lr2",service="auth-service"}',
    'kube_pod_status_phase{namespace="vp-lr2",phase="Running"}',
    'kube_pod_container_status_restarts_total{namespace="vp-lr2",container="auth-service"}',
    'up{namespace="vp-lr2",service="auth-service"}',
]
snapshot = {}
for query in metrics:
    url = 'http://127.0.0.1:9090/api/v1/query?' + urlencode({'query': query})
    with urlopen(url) as response:
        snapshot[query] = json.load(response)
    print(query.split('{')[0], len(snapshot[query]['data']['result']))

url = 'http://127.0.0.1:9090/api/v1/targets?state=active'
with urlopen(url) as response:
    targets = json.load(response)
snapshot['targets_auth_service'] = [
    target for target in targets['data']['activeTargets']
    if target.get('labels', {}).get('service') == 'auth-service'
]
print('targets_auth_service', len(snapshot['targets_auth_service']))
(folder / 'results' / 'metrics_snapshot.json').write_text(
    json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n'
)
