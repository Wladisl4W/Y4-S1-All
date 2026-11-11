"""Make the Lab 5 report from recorded experiments and genuine screenshots."""
import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent
rows = json.loads((ROOT / 'results/summary.json').read_text())['rows']
by_name = {row['name']: row for row in rows}
required = {f'{mode}-r{rate}' for mode in ('off', 'on') for rate in (10, 25, 50, 100, 200, 400)}
required |= {f'keys-{keys}' for keys in (10, 100, 1000)}
required |= {f'ttl-{ttl}' for ttl in (5, 30, 120)}
assert required <= by_name.keys(), 'Все реальные прогоны должны завершиться до создания отчёта'
for name in required:
    assert (ROOT / 'results' / f'{name}.json').exists()
    assert (ROOT / 'results' / f'{name}.prometheus.json').exists()


def good(row):
    return (row['p95_ms'] < 500 and row['errors_percent'] < 1
            and row['dropped_iterations'] == 0
            and row['actual_rps'] >= row['rate'] * 0.95)


best = {}
for mode in ('off', 'on'):
    candidates = [by_name[f'{mode}-r{rate}'] for rate in (10, 25, 50, 100, 200, 400)
                  if good(by_name[f'{mode}-r{rate}'])]
    best[mode] = max(candidates, key=lambda r: r['actual_rps']) if candidates else None

rates = (10, 25, 50, 100, 200, 400)
assert (ROOT / 'results/p95-comparison.png').exists(), 'Сначала построить график из результатов k6'

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin, sec.right_margin = Cm(3), Cm(1.5)
sec.top_margin, sec.bottom_margin = Cm(2), Cm(1.3)
normal = doc.styles['Normal']


def set_times_new_roman(style):
    """Set the actual font, overriding Word's theme font in heading styles."""
    style.font.name = 'Times New Roman'
    rfonts = style._element.get_or_add_rPr().rFonts
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts')
        style._element.get_or_add_rPr().insert(0, rfonts)
    for attr in ('ascii', 'hAnsi', 'eastAsia', 'cs'):
        rfonts.set(qn(f'w:{attr}'), 'Times New Roman')
    for attr in ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme'):
        rfonts.attrib.pop(qn(f'w:{attr}'), None)


set_times_new_roman(normal)
normal.font.size = Pt(14)
normal.font.color.rgb = RGBColor(0, 0, 0)
normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.first_line_indent = Cm(1.25)
normal.paragraph_format.space_after = Pt(5)
for name in ('Title', 'Heading 1'):
    style = doc.styles[name]
    set_times_new_roman(style)
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.font.bold = True
    style.font.size = Pt(16 if name == 'Title' else 14)
    style.paragraph_format.first_line_indent = Cm(0)
    style.paragraph_format.space_before = Pt(10)
    style.paragraph_format.space_after = Pt(5)
    if name == 'Title' and style._element.pPr is not None:
        for border in style._element.pPr.findall(qn('w:pBdr')):
            style._element.pPr.remove(border)


def p(text):
    return doc.add_paragraph(text)


def heading(text):
    doc.add_paragraph(text, style='Heading 1')


def caption(text, above=False):
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.first_line_indent = Cm(0)
    para.paragraph_format.line_spacing = 1
    para.paragraph_format.space_before = Pt(6 if above else 2)
    para.paragraph_format.space_after = Pt(2 if above else 8)
    run = para.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)


figure = 0


def picture(path, text, width=15.5):
    global figure
    source = ROOT / path
    assert source.exists(), source
    figure += 1
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.first_line_indent = Cm(0)
    para.paragraph_format.space_after = Pt(0)
    para.paragraph_format.keep_with_next = True
    para.add_run().add_picture(str(source), width=Cm(width))
    caption(f'Рисунок {figure}. {text}')


table_number = 0


def table(text, headers, values, widths=None, size=9):
    global table_number
    table_number += 1
    caption(f'Таблица {table_number}. {text}', above=True)
    result = doc.add_table(rows=1, cols=len(headers))
    result.style = 'Table Grid'
    result.alignment = WD_TABLE_ALIGNMENT.CENTER
    result.autofit = False
    if widths:
        for col, width in zip(result.columns, widths):
            col.width = Cm(width)
    for i, header in enumerate(headers):
        result.rows[0].cells[i].text = str(header)
    header_properties = result.rows[0]._tr.get_or_add_trPr()
    repeat_header = OxmlElement('w:tblHeader')
    repeat_header.set(qn('w:val'), 'true')
    header_properties.append(repeat_header)
    for values_row in values:
        cells = result.add_row().cells
        for i, value in enumerate(values_row):
            cells[i].text = str(value)
    for row in result.rows:
        for i, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if widths:
                cell.width = Cm(widths[i])
            for para in cell.paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                para.paragraph_format.first_line_indent = Cm(0)
                para.paragraph_format.line_spacing = 1
                para.paragraph_format.space_after = Pt(1)
                for run in para.runs:
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(size)


def f(value, digits=2):
    return f'{value:.{digits}f}' if value is not None else '-'


title = doc.add_paragraph(style='Title')
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.add_run('Лабораторная работа № 5. Кэширование данных с Redis')
if title._p.pPr is not None:
    for border in title._p.pPr.findall(qn('w:pBdr')):
        title._p.pPr.remove(border)
p('Цель работы: проверить, как Redis влияет на задержку, число обращений к медленному источнику и устойчивую пропускную способность приложения.')

heading('1. Приложение и окружение')
p('Я развернул отдельные cache-app и Redis в namespace vp-lr5 прежнего K3s. GET /data/<item_id> без кэша каждый раз ждёт 50 мс и возвращает значение. При cache=on приложение сначала проверяет Redis, при промахе обращается к тому же источнику и сохраняет ответ с TTL. Это стратегия Cache-Aside. Один процесс Gunicorn обрабатывает запросы последовательно. Во всех сериях код, ресурсы Pod и путь через NodePort 30085 одинаковые.')
p('Зависимости контейнера взяты из официального PyPI и сохранены локально: внутри Pod установка из сети не работала. Исходные файлы и порядок запуска приведены в README. Приложение отдаёт /metrics, Prometheus собирает его счётчики и гистограмму.')
picture('screenshots/cluster-pods.png', 'Работающие Pod ЛР5 в терминале Ubuntu')
picture('screenshots/redis-keys.png', 'Проверка Redis после истечения TTL')

heading('2. Методика тестирования')
p('Один сценарий k6 задавал постоянную интенсивность запросов. Идентификаторы перебирались по кругу, поэтому при одинаковом числе ключей оба режима получали одни и те же объекты. Для основного сравнения использованы цели 10, 25, 50, 100, 200 и 400 запросов/с по 60 секунд. Перед каждым прогоном учебный Redis очищался. В режиме cache=on для сравнения пропускной способности я предварительно заполнял десять ключей; TTL оставался 30 секунд. Результаты k6, показания счётчиков до и после прогона и ответы Prometheus сохранены отдельно в results.')
p('Устойчивым считаю уровень с p95 меньше 500 мс, ошибками меньше 1%, без dropped_iterations и с фактическим RPS не ниже 95% цели. Это оценка только проверенной сетки и длительности теста.')
picture('screenshots/off-r50.png', 'Просмотр сохранённого вывода k6 без кэша при цели 50 запросов/с')
picture('screenshots/on-r50.png', 'Просмотр сохранённого вывода k6 с Redis при той же цели')

heading('3. Сравнение без кэша и с Redis')
table('Результаты при одинаковой целевой интенсивности',
      ['Режим', 'Цель, RPS', 'Факт, RPS', 'p50, мс', 'p95, мс', 'p99, мс'],
      [(mode, rate, f(by_name[f'{mode}-r{rate}']['actual_rps']),
        f(by_name[f'{mode}-r{rate}']['p50_ms']),
        f(by_name[f'{mode}-r{rate}']['p95_ms']),
        f(by_name[f'{mode}-r{rate}']['p99_ms']))
       for rate in rates for mode in ('off', 'on')],
      [2, 2.9, 2.9, 2.9, 2.9, 2.9], 10)
doc.add_page_break()
table('Ошибки и пропущенные итерации при тех же нагрузках',
      ['Режим', 'Цель, RPS', 'Ошибки, %', 'Dropped'],
      [(mode, rate, f(by_name[f'{mode}-r{rate}']['errors_percent']),
        by_name[f'{mode}-r{rate}']['dropped_iterations'])
       for rate in rates for mode in ('off', 'on')],
      [3.5, 4, 4.5, 4.5], 11)
picture('results/p95-comparison.png', 'Сравнение p95 по реальным результатам k6', 14.5)
if best['off'] and best['on']:
    speedup = best['on']['actual_rps'] / best['off']['actual_rps']
    table('Максимальные измеренные устойчивые уровни',
          ['Режим', 'Цель, RPS', 'Факт, RPS', 'p95, мс', 'Рост RPS'],
          [('Без кэша', best['off']['rate'], f(best['off']['actual_rps']), f(best['off']['p95_ms']), '1,00'),
           ('С Redis', best['on']['rate'], f(best['on']['actual_rps']), f(best['on']['p95_ms']), f(speedup))],
          [3.2, 3, 3.2, 3.2, 3])
    p(f'Коэффициент роста устойчивого RPS я считал как RPS с Redis / RPS без Redis: {f(speedup)}. В методичке на странице с формулой числитель и знаменатель записаны в обратном порядке, поэтому для роста я использовал это отношение.')
else:
    p('Для одного из режимов устойчивый уровень в проверенной сетке не найден. Поэтому коэффициент роста RPS не вычислялся.')
p('Задержка без Redis включает имитацию обращения к источнику в 50 мс. При попадании в Redis этот вызов не выполняется. Рост RPS следует оценивать вместе с p95, ошибками и пропущенными итерациями, а не по числу отправленных запросов.')
p(f'При одинаковой цели 10 запросов/с p95 без кэша составил {f(by_name["off-r10"]["p95_ms"])} мс, с Redis - {f(by_name["on-r10"]["p95_ms"])} мс. Отношение задержек без Redis / с Redis равно {f(by_name["off-r10"]["p95_ms"] / by_name["on-r10"]["p95_ms"])}. В прогретой серии обращения к источнику уменьшились с {f(by_name["off-r10"]["source_requests"], 0)} до {f(by_name["on-r10"]["source_requests"], 0)} за один опыт.')

heading('4. Разнообразие ключей и эффективность кэша')
p('При одинаковых 10 запросах/с и TTL 30 секунд я проверил 10, 100 и 1000 разных объектов. Опыт с 1000 ключами длился 120 секунд, остальные - 60 секунд: так каждый из 1000 объектов действительно мог быть запрошен. Перед каждой серией Redis очищался, поэтому первые запросы к ключам были промахами. Доля попаданий рассчитана как hits / (hits + misses) по разности счётчиков до и после прогона. Source RPS рассчитан из числа обращений к источнику за фактическое время запуска k6.')
table('Влияние числа разных объектов',
      ['Ключей', 'Hit Ratio, %', 'p95, мс', 'Source RPS', 'Ключей в Redis'],
      [(keys, f(by_name[f'keys-{keys}']['hit_ratio_percent']),
        f(by_name[f'keys-{keys}']['p95_ms']),
        f(by_name[f'keys-{keys}']['source_rps']),
        by_name[f'keys-{keys}']['redis_keys_after']) for keys in (10, 100, 1000)],
      [2.2, 3.4, 3.4, 3.4, 3.2], 10)
picture('screenshots/keys-1000.png', 'Просмотр сохранённого вывода k6 для 1000 объектов')
p(f'При 10 ключах доля попаданий составила {f(by_name["keys-10"]["hit_ratio_percent"])}%, а при 1000 ключах - {f(by_name["keys-1000"]["hit_ratio_percent"])}%. Чем реже повторяется один объект за время TTL, тем меньше пользы от кэша. Длительность серий различалась, поэтому числа обращений к источнику для этого сравнения я перевёл в RPS.')
p(f'После опыта с 1000 объектами команда DBSIZE показывала {by_name["keys-1000"]["redis_keys_after"]} ключей. Это число активных записей на момент проверки, а не число запрошенных объектов: старые записи успели истечь при TTL 30 секунд.')

heading('5. Влияние TTL')
p('При 10 ключах и одинаковой цели 10 запросов/с я сравнил TTL 5, 30 и 120 секунд. Каждый опыт длился 150 секунд, чтобы даже запись с TTL 120 секунд могла истечь. Перед каждым опытом Redis очищался. Большее время жизни уменьшает повторные обращения к источнику, но увеличивает время возможного устаревания значения.')
table('Измерения при разном TTL',
      ['TTL, с', 'Hit Ratio, %', 'Обращений к источнику', 'Source RPS', 'p95, мс'],
      [(ttl, f(by_name[f'ttl-{ttl}']['hit_ratio_percent']),
        f(by_name[f'ttl-{ttl}']['source_requests'], 0),
        f(by_name[f'ttl-{ttl}']['source_rps']),
        f(by_name[f'ttl-{ttl}']['p95_ms'])) for ttl in (5, 30, 120)],
      [2.2, 3.3, 4, 3.1, 3.0], 9)
picture('screenshots/ttl-5.png', 'Просмотр сохранённого вывода k6 при TTL 5 секунд')
p(f'За 150 секунд при TTL 5 с источник получил {f(by_name["ttl-5"]["source_requests"], 0)} обращений, при TTL 120 с - {f(by_name["ttl-120"]["source_requests"], 0)}. Больший TTL экономит обращения, если повторные запросы приходят раньше истечения записи; ценой становится возможное устаревание ответа.')

heading('6. Анализ в Grafana')
p('Dashboard показывает HTTP RPS и p95 по режимам, Hit Ratio, обращения к источнику в секунду, попадания и промахи. На снимках открыт сохранённый период реальных испытаний. При cache=off счётчики попаданий не растут: в этом режиме приложение сразу обращается к источнику.')
picture('screenshots/grafana-throughput.png', 'Grafana: RPS и p95 за период сравнения режимов', 14.5)
picture('screenshots/grafana-cache.png', 'Grafana: Hit Ratio и Source RPS за период исследования кэша', 14.5)
p('Наибольший выигрыш Redis даёт при повторных обращениях к небольшому набору объектов до истечения TTL: тогда Hit Ratio высок, Source RPS низок, а p95 остаётся меньше порога даже при увеличении HTTP RPS. При большом разнообразии ключей промахов становится больше, поэтому обращения к источнику и задержка растут. Кратковременные провалы графика при перегрузке связаны с тем, что однопроцессное приложение поздно отвечало и сборщику метрик; для итоговых чисел я использовал исходные результаты k6.')

heading('Вывод')
if best['off'] and best['on']:
    p(f'Я реализовал Cache-Aside через Redis и измерил работу в двух режимах. В проверенной сетке наибольший устойчивый уровень без кэша составил {f(best["off"]["actual_rps"])} RPS, с Redis - {f(best["on"]["actual_rps"])} RPS. Данные по числу ключей и TTL показывают, как попадания в кэш снижают обращения к источнику. Результат относится к одному процессу приложения и выбранной нагрузке; для более точного предела нужны дополнительные уровни между соседними проверенными точками.')
else:
    p('Я реализовал Cache-Aside через Redis и сохранил результаты сравнения, серий по числу ключей и TTL. В проверенном диапазоне не удалось установить устойчивый уровень для обоих режимов, поэтому численное ускорение не заявляю.')

footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer.paragraph_format.first_line_indent = Cm(0)
field = OxmlElement('w:fldSimple')
field.set(qn('w:instr'), 'PAGE')
footer._p.append(field)
doc.save(ROOT / 'ЛР5_отчёт.docx')
