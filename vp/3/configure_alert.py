"""Create and verify the Grafana alert using the local Grafana API."""

import base64
import json
import os
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = 'http://127.0.0.1:3000'
secret = json.loads(subprocess.check_output(
    ['k3s', 'kubectl', '-n', 'monitoring', 'get', 'secret', 'prometheus-grafana', '-o', 'json'],
    env=os.environ | {'KUBECONFIG': str(Path.home() / '.kube/config')}))
password = base64.b64decode(secret['data']['admin-password']).decode()
auth = 'Basic ' + base64.b64encode(('admin:' + password).encode()).decode()


def api(path, data=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    request = Request(BASE + path, data=body, method=method,
                      headers={'Authorization': auth, 'Content-Type': 'application/json',
                               'X-Disable-Provenance': 'true'})
    try:
        with urlopen(request, timeout=20) as response:
            content = response.read()
            return json.loads(content) if content else {}
    except HTTPError as error:
        raise RuntimeError(f'{path}: HTTP {error.code}: {error.read().decode()[:600]}') from error


folder_uid = 'vp-lr3-alerts'
try:
    api('/api/folders/' + folder_uid)
except RuntimeError:
    api('/api/folders', {'uid': folder_uid, 'title': 'VP LR3'}, 'POST')

expression = ('100 * (sum(rate(http_requests_total{namespace="vp-lr3",'
              'service="auth-service",status=~"5.."}[1m])) or vector(0)) '
              '/ clamp_min(sum(rate(http_requests_total{namespace="vp-lr3",'
              'service="auth-service",route="index"}[1m])), 0.001)')
rule = {
    'uid': 'vp-lr3-error-rate', 'title': 'Error Rate > 1%',
    'folderUID': folder_uid, 'ruleGroup': 'High-load Application', 'orgId': 1,
    'condition': 'C', 'for': '2m', 'noDataState': 'OK', 'execErrState': 'Error',
    'annotations': {'summary': 'Error rate of auth-service exceeds 1% for 2 minutes'},
    'labels': {'lab': 'vp-lr3'},
    'data': [
        {'refId': 'A', 'datasourceUid': 'prometheus', 'queryType': '',
         'relativeTimeRange': {'from': 300, 'to': 0},
         'model': {'expr': expression, 'refId': 'A', 'instant': True,
                   'range': False, 'intervalMs': 1000, 'maxDataPoints': 43200,
                   'datasource': {'type': 'prometheus', 'uid': 'prometheus'}}},
        {'refId': 'B', 'datasourceUid': '__expr__', 'queryType': '',
         'relativeTimeRange': {'from': 0, 'to': 0},
         'model': {'type': 'reduce', 'expression': 'A', 'reducer': 'last',
                   'refId': 'B', 'datasource': {'type': '__expr__', 'uid': '__expr__'}}},
        {'refId': 'C', 'datasourceUid': '__expr__', 'queryType': '',
         'relativeTimeRange': {'from': 0, 'to': 0},
         'model': {'type': 'threshold', 'expression': 'B', 'refId': 'C',
                   'conditions': [{'evaluator': {'params': [1], 'type': 'gt'}}],
                   'datasource': {'type': '__expr__', 'uid': '__expr__'}}},
    ],
}

try:
    existing = api('/api/v1/provisioning/alert-rules/' + rule['uid'])
    print('Existing alert:', existing['title'])
except RuntimeError:
    created = api('/api/v1/provisioning/alert-rules', rule, 'POST')
    print('Created alert:', created['title'])

group_path = f'/api/v1/provisioning/folder/{folder_uid}/rule-groups/High-load%20Application'
group = api(group_path)
group['interval'] = 60
api(group_path, group, 'PUT')
actual = api('/api/v1/provisioning/alert-rules/' + rule['uid'])
group = api(group_path)
assert actual['for'] == '2m' and actual['condition'] == 'C'
assert group['interval'] == 60
print('Verified:', actual['title'], 'for', actual['for'], 'interval', group['interval'], 'seconds')
