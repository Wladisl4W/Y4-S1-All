"""Install, export, and verify the lab dashboard without storing credentials."""

import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


folder = Path(__file__).parent
base = os.environ.get('GRAFANA_URL', 'http://127.0.0.1:3000')
secret = json.loads(subprocess.check_output(
    ['k3s', 'kubectl', '-n', 'monitoring', 'get', 'secret',
     'prometheus-grafana', '-o', 'json'],
    env=os.environ | {'KUBECONFIG': str(Path.home() / '.kube/config')},
))
password = base64.b64decode(secret['data']['admin-password']).decode()
authorization = 'Basic ' + base64.b64encode(('admin:' + password).encode()).decode()


def api(path, data=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    request = Request(base + path, data=body, method=method,
                      headers={'Authorization': authorization,
                               'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(f'{path}: HTTP {error.code}: {error.read().decode()[:500]}') from error


mode = sys.argv[1]
if mode == 'source':
    result = api('/api/datasources/uid/prometheus/health')
    print(result['status'], result['message'])
elif mode == 'install':
    dashboard = json.loads((folder / 'high-load-dashboard.json').read_text())
    result = api('/api/dashboards/db', {'dashboard': dashboard,
                                       'folderUid': '', 'overwrite': True}, 'POST')
    print(result['status'], result['uid'], result['url'])
elif mode == 'export':
    result = api('/api/dashboards/uid/vp-lr3-high-load')
    dashboard = result['dashboard']
    dashboard.pop('id', None)  # instance-specific ID blocks a second import
    (folder / 'high-load-dashboard.json').write_text(
        json.dumps(dashboard, ensure_ascii=False, indent=2) + '\n')
    print('Exported', dashboard['uid'], len(dashboard['panels']), 'panels')
elif mode == 'verify':
    result = api('/api/dashboards/uid/vp-lr3-high-load')
    dashboard = result['dashboard']
    assert len(dashboard['panels']) == 7
    print('Verified', dashboard['uid'], len(dashboard['panels']), 'panels')
elif mode == 'annotate':
    summary = json.loads((folder / 'results/summary.json').read_text())['rows']
    row = next(row for row in summary if row['vus'] == 100)
    from datetime import datetime
    timestamp = int(datetime.fromisoformat(row['start_utc']).timestamp() * 1000)
    result = api('/api/annotations', {
        'dashboardUID': 'vp-lr3-high-load', 'time': timestamp,
        'tags': ['vp-lr3', '100-vu'],
        'text': '100 VU: заметный рост клиентского p95; серверное насыщение не доказано',
    }, 'POST')
    print('Annotation', result['id'], timestamp)
else:
    raise SystemExit(f'unknown mode: {mode}')
