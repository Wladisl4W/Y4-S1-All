"""Update the running Grafana source and install Lab 4 dashboard; no saved password."""
import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parent
env = os.environ | {'KUBECONFIG': str(Path.home() / '.kube/config')}
secret = json.loads(subprocess.check_output(
    ['k3s', 'kubectl', '-n', 'monitoring', 'get', 'secret', 'prometheus-grafana', '-o', 'json'],
    env=env))
password = base64.b64decode(secret['data']['admin-password']).decode()
auth = 'Basic ' + base64.b64encode(f'admin:{password}'.encode()).decode()
base = os.environ.get('GRAFANA_URL', 'http://127.0.0.1:3000')


def api(path, data=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    request = Request(base + path, data=body, method=method,
                      headers={'Authorization': auth, 'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(f'{path}: HTTP {error.code}: {error.read().decode()[:300]}') from error


mode = sys.argv[1]
if mode == 'source':
    source = api('/api/datasources/uid/prometheus')
    print('Prometheus datasource', source['url'])
    result = api('/api/datasources/uid/prometheus/health')
    print(result['status'], result['message'])
elif mode == 'install':
    dashboard = json.loads((root / 'high-load-dashboard-scaling.json').read_text())
    result = api('/api/dashboards/db', {
        'dashboard': dashboard, 'folderUid': '', 'overwrite': True,
    }, 'POST')
    print(result['status'], result['uid'], result['url'])
elif mode == 'export':
    result = api('/api/dashboards/uid/vp-lr4-scaling')['dashboard']
    result.pop('id', None)
    (root / 'high-load-dashboard-scaling.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('exported', result['uid'], len(result['panels']), 'panels')
elif mode == 'verify':
    result = api('/api/dashboards/uid/vp-lr4-scaling')['dashboard']
    assert len(result['panels']) == 10
    print('verified', result['uid'], len(result['panels']), 'panels')
else:
    raise SystemExit('Expected source, install, export or verify')
