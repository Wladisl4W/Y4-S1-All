import json
from pathlib import Path

import matplotlib.pyplot as plt


results_dir = Path(__file__).parent / "results"
names = ["basic", "vu10", "vu25", "vu50", "vu100", "vu200", "vu400", "vu800"]
rows = []

for name in names:
    path = results_dir / f"{name}.json"
    if not path.exists():
        continue

    data = json.loads(path.read_text())
    metrics = data["metrics"]
    duration = metrics["http_req_duration"]
    requests = metrics["http_reqs"]["count"]
    vus = 10 if name == "basic" else int(name[2:])
    rows.append({
        "test": name,
        "vus": vus,
        "requests": requests,
        "rps": requests / 30,
        "p50": duration["med"],
        "p90": duration["p(90)"],
        "p95": duration["p(95)"],
        "p99": duration["p(99)"],
        "errors": metrics["http_req_failed"]["value"] * 100,
        "checks_failed": metrics["checks"]["fails"],
    })

if not rows:
    raise SystemExit("В папке results нет результатов k6. Сначала запустите run_tests.sh")

for row in rows:
    print(f"{row['test']:6} VU={row['vus']:4} RPS={row['rps']:8.2f} "
          f"p95={row['p95']:8.2f} ms errors={row['errors']:.3f}%")

series = [row for row in rows if row["test"] != "basic"]
degradation = None
for previous, current in zip(series, series[1:]):
    causes = []
    if current["p95"] > 2 * previous["p95"]:
        causes.append("p95 вырос более чем вдвое")
    if current["errors"] > 0.1:
        causes.append("ошибки превысили 0,1%")
    if current["vus"] == 2 * previous["vus"] and current["rps"] < 1.1 * previous["rps"]:
        causes.append("RPS вырос менее чем на 10% при удвоении VU")
    if causes:
        degradation = {"vus": current["vus"], "causes": causes}
        break

if degradation:
    print(f"Точка деградации: {degradation['vus']} VU ({'; '.join(degradation['causes'])})")
else:
    print("Точка деградации не обнаружена в измеренном диапазоне")

(results_dir / "summary.json").write_text(
    json.dumps({"rows": rows, "degradation": degradation}, ensure_ascii=False, indent=2)
)

if series:
    vus = [row["vus"] for row in series]
    p95 = [row["p95"] for row in series]

    plt.figure(figsize=(8, 4.5))
    plt.plot(vus, p95, marker="o")
    plt.xlabel("Виртуальные пользователи, VU")
    plt.ylabel("p95 задержки, мс")
    plt.title("Задержка ответа при увеличении нагрузки")
    plt.grid(True, alpha=0.3)
    if degradation:
        point = next(row for row in series if row["vus"] == degradation["vus"])
        plt.scatter([point["vus"]], [point["p95"]], color="red", zorder=3)
        plt.annotate("Точка деградации", (point["vus"], point["p95"]),
                     xytext=(10, 10), textcoords="offset points")
    plt.tight_layout()
    plt.savefig(results_dir / "latency_vs_load.png", dpi=180)
    plt.close()

    plt.figure(figsize=(8, 4.5))
    plt.plot(vus, [row["rps"] for row in series], marker="o")
    plt.xlabel("Виртуальные пользователи, VU")
    plt.ylabel("Запросов в секунду, RPS")
    plt.title("Пропускная способность при увеличении нагрузки")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(results_dir / "rps_vs_load.png", dpi=180)
    plt.close()
