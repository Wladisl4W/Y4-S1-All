"""Use the current Kubernetes Secret only in memory for Grafana API calls."""
import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
ENV = os.environ | {'KUBECONFIG': str(Path.home() / '.kube/config')}
secret = json.loads(subprocess.check_output([
    'k3s', 'kubectl', '-n', 'monitoring', 'get', 'secret',
    'prometheus-grafana', '-o', 'json'], env=ENV))
password = base64.b64decode(secret['data']['admin-password']).decode()
auth = 'Basic ' + base64.b64encode(f'admin:{password}'.encode()).decode()
base = os.environ.get('GRAFANA_URL', 'http://127.0.0.1:13000')


def api(path, data=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    with urlopen(Request(base + path, data=body, method=method,
                         headers={'Authorization': auth, 'Content-Type': 'application/json'}),
                 timeout=20) as response:
        return json.load(response)


mode = sys.argv[1]
if mode == 'source':
    pod_ip = subprocess.check_output([
        'k3s', 'kubectl', '-n', 'monitoring', 'get', 'pod',
        'prometheus-prometheus-kube-prometheus-prometheus-0',
        '-o', 'jsonpath={.status.podIP}'], env=ENV, text=True).strip()
    try:
        source = api('/api/datasources/uid/prometheus-lr5')
    except HTTPError as error:
        if error.code != 404:
            raise
        source = None
    if source:
        source['url'] = f'http://{pod_ip}:9090/'
        api('/api/datasources/uid/prometheus-lr5', source, 'PUT')
    else:
        api('/api/datasources', {'name': 'Prometheus LR5', 'type': 'prometheus',
                                 'uid': 'prometheus-lr5', 'access': 'proxy',
                                 'url': f'http://{pod_ip}:9090/', 'isDefault': False}, 'POST')
    print(api('/api/datasources/uid/prometheus-lr5/health'))
elif mode == 'install':
    dashboard = json.loads((ROOT / 'cache-dashboard.json').read_text())
    print(api('/api/dashboards/db', {'dashboard': dashboard, 'folderUid': '',
                                    'overwrite': True}, 'POST'))
elif mode == 'export':
    result = api('/api/dashboards/uid/vp-lr5-cache')['dashboard']
    result.pop('id', None)
    (ROOT / 'cache-dashboard.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('exported', result['uid'], len(result['panels']))
elif mode == 'verify':
    result = api('/api/dashboards/uid/vp-lr5-cache')['dashboard']
    assert len(result['panels']) == 6
    print('verified', result['uid'], len(result['panels']))
else:
    raise SystemExit('Expected source, install, export, or verify')
