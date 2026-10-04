import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


folder = Path(__file__).parent
results = folder / "results"
rows = []

for vus in (10, 50, 200):
    k6 = json.loads((results / f"vu{vus}.json").read_text())
    prom = json.loads((results / f"vu{vus}.prometheus.json").read_text())
    metrics = k6["metrics"]
    averages = prom["averages"]
    rows.append({
        "vus": vus,
        "requests": metrics["http_reqs"]["count"],
        "rps": metrics["http_reqs"]["rate"],
        "p95_k6_ms": metrics["http_req_duration"]["p(95)"],
        "p99_k6_ms": metrics["http_req_duration"]["p(99)"],
        "errors_percent": metrics["http_req_failed"]["value"] * 100,
        "cpu_percent_of_one_core": averages["cpu_percent_of_one_core"],
        "memory_mib": averages["memory_mib"],
        "p95_prometheus_ms": averages["prometheus_p95_ms"],
        "p99_prometheus_ms": averages["prometheus_p99_ms"],
        "start_utc": prom["start_utc"],
        "end_utc": prom["end_utc"],
    })

point = rows[-1]
comparison = {
    "vus": point["vus"],
    "difference_ms": point["p95_k6_ms"] - point["p95_prometheus_ms"],
    "difference_percent_of_k6": (
        (point["p95_k6_ms"] - point["p95_prometheus_ms"])
        / point["p95_k6_ms"] * 100
    ),
}
(results / "summary.json").write_text(
    json.dumps({"rows": rows, "comparison": comparison}, ensure_ascii=False, indent=2) + "\n"
)

loads = [row["vus"] for row in rows]

plt.figure(figsize=(8, 4.5))
plt.plot(loads, [row["p95_k6_ms"] for row in rows], "o-", label="k6, с клиента")
plt.plot(loads, [row["p95_prometheus_ms"] for row in rows], "s-", label="Prometheus, в приложении")
plt.xticks(loads)
plt.xlabel("Виртуальные пользователи, VU")
plt.ylabel("p95, мс")
plt.title("Время ответа при росте нагрузки")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(results / "p95.png", dpi=180)
plt.close()

fig, left = plt.subplots(figsize=(8, 4.5))
left.plot(loads, [row["cpu_percent_of_one_core"] for row in rows], "o-", color="#1769a3")
left.set_ylabel("CPU, % одного ядра", color="#1769a3")
left.set_xlabel("Виртуальные пользователи, VU")
left.set_xticks(loads)
left.grid(alpha=0.3)
right = left.twinx()
right.plot(loads, [row["memory_mib"] for row in rows], "s-", color="#bf5a36")
right.set_ylabel("Память, МиБ", color="#bf5a36")
plt.title("Ресурсы auth-service")
fig.tight_layout()
fig.savefig(results / "resources.png", dpi=180)
plt.close(fig)

plt.figure(figsize=(8, 4.5))
plt.plot(loads, [row["rps"] for row in rows], "o-", color="#18805d")
plt.xticks(loads)
plt.xlabel("Виртуальные пользователи, VU")
plt.ylabel("Запросов в секунду, RPS")
plt.title("Пропускная способность")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(results / "rps.png", dpi=180)
plt.close()

for row in rows:
    print(
        f"{row['vus']:>3} VU: {row['rps']:.2f} RPS, "
        f"k6 p95 {row['p95_k6_ms']:.2f} мс, "
        f"Prometheus p95 {row['p95_prometheus_ms']:.2f} мс, "
        f"CPU {row['cpu_percent_of_one_core']:.1f}%, "
        f"память {row['memory_mib']:.1f} МиБ"
    )
