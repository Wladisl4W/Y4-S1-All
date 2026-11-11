"""Plot the measured p95 values from the saved k6 summaries."""
import json
from pathlib import Path

import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent
rows = json.loads((root / 'results/summary.json').read_text())['rows']
by_name = {row['name']: row for row in rows}
rates = (10, 25, 50, 100, 200, 400)

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
fig, ax = plt.subplots(figsize=(8, 4.4))
for mode, label in (('off', 'Без Redis'), ('on', 'С Redis')):
    ax.plot(rates, [by_name[f'{mode}-r{rate}']['p95_ms'] for rate in rates],
            marker='o', label=label)
ax.axhline(500, color='gray', linestyle='--', label='Порог 500 мс')
ax.set(xlabel='Целевые запросы/с', ylabel='p95, мс',
       title='Задержка по исходным результатам k6')
ax.set_yscale('log')
ax.grid(True, which='both', alpha=.3)
ax.legend()
fig.tight_layout()
fig.savefig(root / 'results/p95-comparison.png', dpi=180)
plt.close(fig)
