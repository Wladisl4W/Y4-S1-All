"""Create the seven-panel Grafana dashboard for the measured auth-service."""

import json
from pathlib import Path


folder = Path(__file__).parent
source = {"type": "prometheus", "uid": "prometheus"}
selector = 'namespace="$namespace",pod=~"$pod"'


def panel(number, title, expr, kind, unit, x, y, width=12, height=7,
          mappings=None, thresholds=None):
    defaults = {"unit": unit, "color": {"mode": "palette-classic"}}
    if mappings:
        defaults["mappings"] = mappings
    if thresholds:
        defaults["thresholds"] = thresholds
    return {
        "id": number, "title": title, "type": kind,
        "datasource": source, "gridPos": {"x": x, "y": y, "w": width, "h": height},
        "targets": [{"refId": "A", "expr": expr, "datasource": source,
                     "editorMode": "code", "legendFormat": title}],
        "fieldConfig": {"defaults": defaults, "overrides": []},
        "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}}
        if kind == "stat" else {},
    }


rps = f'sum(rate(http_requests_total{{{selector},route="index"}}[1m]))'
errors = f'sum(rate(http_requests_total{{{selector},status=~"5.."}}[1m])) or vector(0)'
error_rate = f'100 * ({errors}) / clamp_min({rps}, 0.001)'
p95 = (f'histogram_quantile(0.95, sum by (le) '
       f'(rate(http_request_duration_seconds_bucket{{{selector},route="index"}}[1m])))')
cpu = f'sum(rate(container_cpu_usage_seconds_total{{{selector},container="auth-service"}}[1m]))'
memory = f'sum(container_memory_working_set_bytes{{{selector},container="auth-service"}}) / 1024 / 1024'
up = f'up{{{selector},service="auth-service"}}'

panels = [
    panel(1, "RPS", rps, "timeseries", "reqps", 0, 0),
    panel(2, "HTTP 5xx Errors", errors, "timeseries", "reqps", 12, 0),
    panel(3, "Error Rate", error_rate, "timeseries", "percent", 0, 7,
          thresholds={"mode": "absolute", "steps": [{"color": "green", "value": None},
                                                    {"color": "red", "value": 1}]}),
    panel(4, "p95 Latency", p95, "timeseries", "s", 12, 7),
    panel(5, "CPU Usage", cpu, "timeseries", "cores", 0, 14),
    panel(6, "Memory Usage", memory, "timeseries", "mbytes", 12, 14),
    panel(7, "Pod Status", up, "stat", "none", 0, 21, 24, 4,
          mappings=[{"type": "value", "options": {
              "1": {"text": "UP", "color": "green"},
              "0": {"text": "DOWN", "color": "red"}}}]),
]

dashboard = {
    "uid": "vp-lr3-high-load", "title": "High-load Application",
    "tags": ["vp-lr3", "laboratory"], "timezone": "browser",
    "schemaVersion": 41, "version": 0, "refresh": "5s",
    "time": {"from": "now-15m", "to": "now"},
    "templating": {"list": [
        {"name": "namespace", "label": "namespace", "type": "query",
         "datasource": source, "query": {"query": "label_values(up, namespace)",
                                           "refId": "PrometheusVariableQueryEditor-VariableQuery"},
         "refresh": 1, "current": {"text": "vp-lr3", "value": "vp-lr3"},
         "sort": 1, "hide": 0},
        {"name": "pod", "label": "pod", "type": "query", "datasource": source,
         "query": {"query": 'label_values(up{namespace="$namespace",service="auth-service"}, pod)',
                   "refId": "PrometheusVariableQueryEditor-VariableQuery"},
         "refresh": 1, "includeAll": True, "allValue": ".*",
         "current": {"text": "All", "value": "$__all"}, "sort": 1, "hide": 0},
    ]},
    "panels": panels,
}

(folder / 'high-load-dashboard.json').write_text(
    json.dumps(dashboard, ensure_ascii=False, indent=2) + '\n'
)
