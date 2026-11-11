"""Build the Grafana dashboard from the actual cache-app metric labels."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
data_source = {'type': 'prometheus', 'uid': 'prometheus-lr5'}


def panel(number, title, expression, unit, x, y, legend):
    return {
        'id': number, 'type': 'timeseries', 'title': title,
        'gridPos': {'h': 8, 'w': 12, 'x': x, 'y': y},
        'fieldConfig': {'defaults': {'color': {'mode': 'palette-classic'}, 'unit': unit}, 'overrides': []},
        'options': {},
        'targets': [{'datasource': data_source, 'editorMode': 'code',
                     'expr': expression, 'legendFormat': legend, 'refId': 'A'}],
    }


dashboard = {
    'uid': 'vp-lr5-cache', 'title': 'Cache Aside - Redis Lab 5',
    'schemaVersion': 41, 'version': 1, 'refresh': '5s',
    'tags': ['vp-lr5', 'redis'], 'timezone': 'browser',
    'time': {'from': 'now-15m', 'to': 'now'},
    'templating': {'list': [
        {'name': 'namespace', 'label': 'namespace', 'type': 'query',
         'datasource': data_source, 'query': {'query': 'label_values(up, namespace)', 'refId': 'PrometheusVariableQueryEditor-VariableQuery'},
         'current': {'text': 'vp-lr5', 'value': 'vp-lr5'}, 'refresh': 1, 'sort': 1},
        {'name': 'mode', 'label': 'mode', 'type': 'custom', 'query': 'All : .*,on : on,off : off',
         'current': {'text': 'All', 'value': '.*'}, 'options': [
             {'text': 'All', 'value': '.*', 'selected': True},
             {'text': 'on', 'value': 'on', 'selected': False},
             {'text': 'off', 'value': 'off', 'selected': False}]},
    ]},
    'panels': [
        panel(1, 'HTTP RPS by mode',
              'sum by (mode) (rate(app_http_requests_total{namespace="$namespace",mode=~"$mode"}[15s]))',
              'reqps', 0, 0, '{{mode}}'),
        panel(2, 'p95 Latency by mode',
              'histogram_quantile(0.95, sum by (le, mode) (rate(app_http_request_duration_seconds_bucket{namespace="$namespace",mode=~"$mode"}[15s])))',
              's', 12, 0, '{{mode}}'),
        panel(3, 'Cache Hit Ratio',
              '100 * sum(rate(cache_hits_total{namespace="$namespace"}[15s])) / (sum(rate(cache_hits_total{namespace="$namespace"}[15s])) + sum(rate(cache_misses_total{namespace="$namespace"}[15s])))',
              'percent', 0, 8, 'Hit Ratio'),
        panel(4, 'Source RPS',
              'sum(rate(source_requests_total{namespace="$namespace"}[15s]))',
              'reqps', 12, 8, 'Source RPS'),
        panel(5, 'Cache Hits and Misses',
              'sum(rate(cache_hits_total{namespace="$namespace"}[15s]))',
              'reqps', 0, 16, 'Hits'),
        panel(6, 'HTTP Error Rate by mode',
              '100 * sum by (mode) (rate(app_http_requests_total{namespace="$namespace",mode=~"$mode",status=~"[45].."}[15s])) / sum by (mode) (rate(app_http_requests_total{namespace="$namespace",mode=~"$mode"}[15s]))',
              'percent', 12, 16, '{{mode}}'),
    ],
}
dashboard['panels'][4]['targets'].append({
    'datasource': data_source, 'editorMode': 'code',
    'expr': 'sum(rate(cache_misses_total{namespace="$namespace"}[15s]))',
    'legendFormat': 'Misses', 'refId': 'B',
})
(ROOT / 'cache-dashboard.json').write_text(json.dumps(dashboard, ensure_ascii=False, indent=2) + '\n')
