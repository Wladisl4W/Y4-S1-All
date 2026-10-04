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
results = folder / "results"
results.mkdir(exist_ok=True)

prometheus = os.environ.get("PROMETHEUS_URL", "http://127.0.0.1:9090")
target = os.environ.get("TARGET_URL", "http://127.0.0.1:30081/")

queries = {
    "cpu_percent": '100 * sum(rate(container_cpu_usage_seconds_total{namespace="vp-lr2",container="auth-service"}[20s]))',
    "memory_mib": 'sum(container_memory_working_set_bytes{namespace="vp-lr2",container="auth-service"}) / 1024 / 1024',
    "rps": 'sum(rate(http_requests_total{namespace="vp-lr2",route="index"}[15s]))',
    "errors_5xx": 'sum(rate(http_errors_total{namespace="vp-lr2",group="5xx"}[15s])) or vector(0)',
    "p95_ms": '1000 * histogram_quantile(0.95, sum by (le) (increase(http_request_duration_seconds_bucket{namespace="vp-lr2",route="index"}[40s])))',
    "p99_ms": '1000 * histogram_quantile(0.99, sum by (le) (increase(http_request_duration_seconds_bucket{namespace="vp-lr2",route="index"}[40s])))',
}


def api(path, parameters):
    url = prometheus + path + "?" + urlencode(parameters)
    with urlopen(url, timeout=20) as response:
        data = json.load(response)
    if data["status"] != "success":
        raise RuntimeError(f"Prometheus error: {data}")
    return data


def numbers(response):
    values = []
    for series in response["data"]["result"]:
        points = series.get("values", [series.get("value")])
        for point in points:
            if point is None:
                continue
            value = float(point[1])
            if math.isfinite(value):
                values.append(value)
    return values


up = api("/api/v1/query", {"query": 'up{namespace="vp-lr2",service="auth-service"}'})
if 1.0 not in numbers(up):
    raise RuntimeError("Prometheus не видит auth-service (up != 1)")

for vus in (10, 50, 200):
    if vus != 10:
        time.sleep(40)

    name = f"vu{vus}"
    environment = os.environ.copy()
    environment.update({"VUS": str(vus), "DURATION": "30s", "TARGET_URL": target})
    start = time.time()
    with (results / f"{name}.txt").open("w") as output:
        process = subprocess.run(
            ["k6", "run", "--summary-export", str(results / f"{name}.json"), "test.js"],
            cwd=folder, env=environment, stdout=output, stderr=subprocess.STDOUT,
        )
    end = time.time()
    if process.returncode != 0:
        raise RuntimeError(f"k6 завершился с ошибкой: {name}")

    time.sleep(6)
    responses = {}
    for key in ("cpu_percent", "memory_mib", "rps", "errors_5xx"):
        responses[key] = api("/api/v1/query_range", {
            "query": queries[key], "start": start + 15, "end": end,
            "step": 5,
        })
    for key in ("p95_ms", "p99_ms"):
        responses[key] = api("/api/v1/query", {
            "query": queries[key], "time": end + 5,
        })

    raw = {
        "vus": vus,
        "start_utc": datetime.fromtimestamp(start, timezone.utc).isoformat(),
        "end_utc": datetime.fromtimestamp(end, timezone.utc).isoformat(),
        "target_url": target,
        "queries": queries,
        "responses": responses,
    }
    path = results / f"{name}.prometheus.json"
    path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n")

    cpu = numbers(responses["cpu_percent"])
    memory = numbers(responses["memory_mib"])
    p95 = numbers(responses["p95_ms"])
    if not cpu or not memory or not p95:
        raise RuntimeError(f"Нет метрик CPU, памяти или p95 для {name}")

    record = raw
    record["averages"] = {
        "cpu_percent_of_one_core": statistics.mean(cpu),
        "memory_mib": statistics.mean(memory),
        "prometheus_p95_ms": p95[0],
        "prometheus_p99_ms": numbers(responses["p99_ms"])[0],
    }
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    summary = json.loads((results / f"{name}.json").read_text())
    print(
        f"{vus} VU: {summary['metrics']['http_reqs']['count']} requests, "
        f"CPU {record['averages']['cpu_percent_of_one_core']:.1f}%, "
        f"memory {record['averages']['memory_mib']:.1f} MiB",
        flush=True,
    )
