import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

folder = Path(__file__).parent
rows = list(csv.DictReader((folder / 'connectivity.csv').open()))
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
fig, ax = plt.subplots(figsize=(8.2, 5.2))
for radius in [25, 35, 45, 55, 65]:
    series = [row for row in rows if int(float(row['r'])) == radius]
    ax.plot([int(row['n']) for row in series],
            [float(row['probability']) for row in series],
            marker='o', markevery=5, markersize=4, linewidth=2,
            label=f'r = {radius}')
ax.set(xlabel='Количество узлов n', ylabel='Вероятность связности',
       xlim=(5, 40), ylim=(0, 1.02))
ax.set_xticks(range(5, 41, 5))
ax.set_yticks([i / 10 for i in range(11)])
ax.grid(alpha=0.3)
ax.legend(title='Радиус связи')
fig.tight_layout()
fig.savefig(folder / 'connectivity.png', dpi=200)
