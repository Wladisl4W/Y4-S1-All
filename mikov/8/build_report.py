import csv
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

folder = Path(__file__).parent
rows = list(csv.DictReader((folder / 'connectivity.csv').open()))
trials = int(rows[0]['total'])
trials_text = f'{trials:,}'.replace(',', ' ')
def probability_at(n, radius):
    value = next(float(row['probability']) for row in rows
                 if int(row['n']) == n and int(float(row['r'])) == radius)
    return f'{value:.4f}'.replace('.', ',')
doc = Document()
section = doc.sections[0]
section.page_width = Cm(21)
section.page_height = Cm(29.7)
section.left_margin = Cm(3)
section.right_margin = Cm(1.5)
section.top_margin = Cm(2)
section.bottom_margin = Cm(1.5)
normal = doc.styles['Normal']
normal.font.name = 'Times New Roman'
normal.font.size = Pt(14)
normal.font.color.rgb = RGBColor(0, 0, 0)
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.first_line_indent = Cm(1.25)
normal.paragraph_format.space_after = Pt(4)
heading = doc.styles['Heading 1']
heading.font.name = 'Times New Roman'
heading.font.size = Pt(14)
heading.font.bold = True
heading.font.color.rgb = RGBColor(0, 0, 0)
doc.styles['Heading 1 Char'].font.color.rgb = RGBColor(0, 0, 0)
doc.styles['Heading 1 Char'].font.name = 'Times New Roman'
doc.styles['Title'].font.color.rgb = RGBColor(0, 0, 0)
doc.styles['Title'].font.name = 'Times New Roman'
doc.styles['Title Char'].font.color.rgb = RGBColor(0, 0, 0)
doc.styles['Title Char'].font.name = 'Times New Roman'
heading.paragraph_format.space_before = Pt(9)
heading.paragraph_format.space_after = Pt(4)

def paragraph(text):
    return doc.add_paragraph(text)

def caption(text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    for run in p.runs:
        run.font.size = Pt(12)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Cm(0)
run = p.add_run('Лабораторная работа 8. Связность беспроводной сети со стенкой')
run.font.name = 'Times New Roman'
run.font.size = Pt(16)
run.font.bold = True
run.font.color.rgb = RGBColor(0, 0, 0)
paragraph('Цель работы: оценить, как количество узлов и радиус связи влияют на вероятность связности беспроводной сети в круге с непроницаемой стенкой.')
doc.add_heading('1. Постановка задачи', 1)
paragraph('Область сети представляет собой круг радиуса R=60. Внутри него размещаются n узлов. Стенка идёт от центра до правой точки окружности, то есть занимает один радиус круга. Сигнал не проходит через стенку. Я менял количество узлов n от 5 до 40 и радиус связи r: 25, 35, 45, 55 и 65.')
paragraph('Два узла соединены напрямую, если расстояние между ними не превышает r и прямая между ними не пересекает стенку. Сеть связна, когда от любого узла можно добраться до любого другого по одному или нескольким соединениям.')
doc.add_heading('2. Метод моделирования', 1)
paragraph(f'Для каждой пары n и r я создал {trials_text} независимых сетей. Узлы размещаются равномерно по площади круга: угол выбирается равномерно от 0 до 2π, а расстояние от центра равно R·√U, где U равномерно на отрезке от 0 до 1. Корень нужен, чтобы не сосредоточить слишком много точек у центра.')
paragraph(f'В каждой сети программа строит граф. Затем она обходит его от первого узла и считает число достигнутых узлов. Если достигнуты все n узлов, сеть связна. Оценка вероятности равна числу связных сетей, делённому на {trials_text}. Результаты сохранены в connectivity.csv.')
h = doc.add_heading('3. Результаты', 1)
h.paragraph_format.page_break_before = True
caption('Таблица 1. Оценка вероятности связности')
table = doc.add_table(rows=1, cols=6)
table.style = 'Table Grid'
table.alignment = WD_TABLE_ALIGNMENT.CENTER
for cell, value in zip(table.rows[0].cells, ['n', 'r=25', 'r=35', 'r=45', 'r=55', 'r=65']):
    cell.text = value
for n in [5, 10, 20, 30, 40]:
    cells = table.add_row().cells
    cells[0].text = str(n)
    for index, radius in enumerate([25, 35, 45, 55, 65], 1):
        cells[index].text = probability_at(n, radius)
for row in table.rows:
    for cell in row.cells:
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Cm(0)
            for run in p.runs:
                run.font.size = Pt(10)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Cm(0)
p.paragraph_format.keep_with_next = True
p.add_run().add_picture(str(folder / 'connectivity.png'), width=Cm(13.5))
caption('Рисунок 1. Вероятность связности при пяти радиусах связи')
paragraph(f'При n=20 оценка составляет {probability_at(20, 25)} для r=25 и {probability_at(20, 65)} для r=65. При фиксированном радиусе связь обычно становится вероятнее с ростом числа узлов. Отдельные соседние точки могут немного снижаться из-за случайности опытов и потому, что новый узел тоже должен быть подключён к сети.')
doc.add_heading('4. Вывод', 1)
paragraph('Я построил графы случайных беспроводных сетей и оценил их связность. Больший радиус связи заметно повышает вероятность связной сети. Стенка блокирует прямые соединения через один радиус круга, но путь между узлами может проходить через другие узлы в обход её конца у центра.')
footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer.paragraph_format.first_line_indent = Cm(0)
field = OxmlElement('w:fldSimple')
field.set(qn('w:instr'), 'PAGE')
footer._p.append(field)
for paragraph in doc.paragraphs:
    if paragraph.style.name.startswith('Heading'):
        for run in paragraph.runs:
            run.font.color.rgb = RGBColor(0, 0, 0)
            run.font.name = 'Times New Roman'
doc.save(folder / 'ЛР8_отчёт.docx')
