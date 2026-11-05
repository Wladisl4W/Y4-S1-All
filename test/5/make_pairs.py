import csv
import itertools
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

ROOT = Path(__file__).resolve().parent
NAMES = [
    ['Intel i5', 'Intel i7', 'AMD Ryzen 7'],
    ['8 ГБ', '16 ГБ', '32 ГБ'],
    ['SSD 256 ГБ', 'SSD 512 ГБ', 'SSD 1 ТБ', 'HDD 1 ТБ'],
    ['Интегрированная', 'NVIDIA GTX 1650', 'NVIDIA RTX 3060'],
]


def allowed(row):
    processor, memory, drive, _ = row
    return not (processor == 0 and memory == 2) and not (processor == 1 and drive == 3)


def pairs(row):
    return {(i, row[i], j, row[j]) for i, j in itertools.combinations(range(4), 2)}


all_rows = list(itertools.product(*(range(len(values)) for values in NAMES)))
valid_rows = [row for row in all_rows if allowed(row)]
universe = sorted(set().union(*(pairs(row) for row in valid_rows)))

# Каждая допустимая конфигурация — возможный тест; каждую пару нужен покрыть хотя бы раз.
matrix = lil_matrix((len(universe), len(valid_rows)), dtype=float)
pair_index = {pair: i for i, pair in enumerate(universe)}
for column, row in enumerate(valid_rows):
    for pair in pairs(row):
        matrix[pair_index[pair], column] = 1

result = milp(
    c=np.ones(len(valid_rows)),
    integrality=np.ones(len(valid_rows)),
    bounds=Bounds(0, 1),
    constraints=LinearConstraint(matrix.tocsr(), 1, np.inf),
    options={'time_limit': 60},
)
if result.status != 0 or result.mip_gap != 0:
    raise RuntimeError(f'Оптимальность не доказана: {result.message}')
chosen = [row for i, row in enumerate(valid_rows) if result.x[i] > 0.5]
covered = set().union(*(pairs(row) for row in chosen))
assert len(all_rows) == 108 and len(valid_rows) == 87
assert len(chosen) == 12 and len(universe) == 61 and covered == set(universe)
assert all(allowed(row) for row in chosen)

with (ROOT / 'pairwise.csv').open('w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['№', 'Процессор', 'ОЗУ', 'Накопитель', 'Видеокарта'])
    for number, row in enumerate(chosen, 1):
        writer.writerow([number] + [NAMES[i][value] for i, value in enumerate(row)])

summary = (
    f'Полный перебор: {len(all_rows)}. Допустимых конфигураций: {len(valid_rows)}.\n'
    f'Попарный набор: {len(chosen)} тестов. Покрытие допустимых пар: {len(covered)}/{len(universe)}.\n'
    f'Точный поиск: нижняя граница {result.mip_dual_bound:.0f}, верхняя граница {result.fun:.0f}, '
    f'разрыв {result.mip_gap:.0%}. Оптимальность доказана.\n'
    'Запрет «интегрированная и RTX 3060 одновременно» не вычитает комбинации: '
    'видеокарта — один параметр с одним выбранным значением.\n'
)
(ROOT / 'coverage.txt').write_text(summary, encoding='utf-8')
print(summary, end='')
