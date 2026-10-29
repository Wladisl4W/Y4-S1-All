"""Adapt the Lab 3 dashboard to the Lab 4 work endpoint and scaling metrics."""
import copy
import json
from pathlib import Path

root = Path(__file__).resolve().parent
dashboard = json.loads((root / 'high-load-dashboard-lr3.json').read_text())
dashboard['title'] = 'High-load Application - Scaling'
dashboard['uid'] = 'vp-lr4-scaling'
dashboard['tags'] = ['vp-lr4', 'scaling']
dashboard['templating']['list'][0]['current'] = {'text': 'vp-lr4', 'value': 'vp-lr4'}
for panel in dashboard['panels']:
    for target in panel['targets']:
        target['expr'] = target['expr'].replace('route="index"', 'route="work"')

reference = copy.deepcopy(dashboard['panels'][0])
extras = [
    ('Available Replicas', 'kube_deployment_status_replicas_available{namespace="$namespace",deployment="auth-service"}', 'none'),
    ('RPS by Pod', 'sum by (pod) (rate(work_requests_total{namespace="$namespace",pod=~"$pod"}[1m]))', 'reqps'),
    ('CPU by Pod', 'sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="$namespace",pod=~"$pod",container="auth-service"}[1m]))', 'short'),
]
for index, (title, expr, unit) in enumerate(extras, 8):
    panel = copy.deepcopy(reference)
    panel['id'] = index
    panel['title'] = title
    panel['targets'][0]['expr'] = expr
    panel['gridPos'] = {'h': 8, 'w': 12, 'x': 0 if index % 2 == 0 else 12,
                        'y': 32 + ((index - 8) // 2) * 8}
    panel.setdefault('fieldConfig', {}).setdefault('defaults', {})['unit'] = unit
    dashboard['panels'].append(panel)

(root / 'high-load-dashboard-scaling.json').write_text(
    json.dumps(dashboard, ensure_ascii=False, indent=2) + '\n')
