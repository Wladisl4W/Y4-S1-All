import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor


folder = Path(__file__).parent
results = folder / "results"
screenshots = results / "screenshots"
summary = json.loads((results / "summary.json").read_text())
rows = summary["rows"]
basic = next(row for row in rows if row["test"] == "basic")
series = [row for row in rows if row["test"] != "basic"]


def figure(doc, path, caption, width=160):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Mm(0)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Mm(width))
    doc.add_paragraph(caption, "Caption")


def paragraph(doc, text):
    doc.add_paragraph(text)


def table(doc):
    doc.add_paragraph("Таблица 1. Результаты испытаний", "Caption")
    headers = ["VU", "RPS", "p50, мс", "p90, мс", "p95, мс", "p99, мс", "Ошибки, %"]
    t = doc.add_table(rows=1, cols=7)
    for i, value in enumerate(headers):
        t.rows[0].cells[i].text = value
    for row in series:
        cells = t.add_row().cells
        values = [row["vus"], f"{row['rps']:.2f}", f"{row['p50']:.2f}",
                  f"{row['p90']:.2f}", f"{row['p95']:.2f}",
                  f"{row['p99']:.2f}", f"{row['errors']:.3f}"]
        for i, value in enumerate(values):
            cells[i].text = str(value)
    for j, row in enumerate(t.rows):
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pr = cell._tc.get_or_add_tcPr()
            borders = OxmlElement("w:tcBorders")
            for edge in ("top", "left", "bottom", "right"):
                item = OxmlElement(f"w:{edge}")
                item.set(qn("w:val"), "single")
                item.set(qn("w:sz"), "4")
                borders.append(item)
            pr.append(borders)
            if j == 0:
                shading = OxmlElement("w:shd")
                shading.set(qn("w:fill"), "EEEEEE")
                pr.append(shading)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.first_line_indent = Mm(0)
                p.paragraph_format.line_spacing = 1
                for run in p.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(10)
                    run.bold = False


doc = Document()
section = doc.sections[0]
section.page_width, section.page_height = Mm(210), Mm(297)
section.left_margin, section.right_margin = Mm(30), Mm(15)
section.top_margin, section.bottom_margin = Mm(20), Mm(20)

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(14)
normal.font.color.rgb = RGBColor(0, 0, 0)
normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
normal.paragraph_format.first_line_indent = Mm(12.5)
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(0)

title = doc.styles["Title"]
title.font.name = "Times New Roman"
title.font.size = Pt(16)
title.font.bold = True
title.font.color.rgb = RGBColor(0, 0, 0)
title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.paragraph_format.first_line_indent = Mm(0)
title.paragraph_format.space_after = Pt(12)
title_pr = title.element.get_or_add_pPr()
border = title_pr.find(qn("w:pBdr"))
if border is not None:
    title_pr.remove(border)

heading = doc.styles["Heading 1"]
heading.font.name = "Times New Roman"
heading.font.size = Pt(14)
heading.font.bold = True
heading.font.color.rgb = RGBColor(0, 0, 0)
heading.paragraph_format.first_line_indent = Mm(0)
heading.paragraph_format.space_before = Pt(12)
heading.paragraph_format.space_after = Pt(6)
heading.paragraph_format.keep_with_next = True

caption = doc.styles["Caption"]
caption.font.name = "Times New Roman"
caption.font.size = Pt(12)
caption.font.bold = False
caption.font.color.rgb = RGBColor(0, 0, 0)
caption.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
caption.paragraph_format.first_line_indent = Mm(0)
caption.paragraph_format.line_spacing = 1
caption.paragraph_format.space_after = Pt(8)

footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer.paragraph_format.first_line_indent = Mm(0)
field = OxmlElement("w:fldSimple")
field.set(qn("w:instr"), "PAGE")
footer._p.append(field)

doc.add_paragraph("Лабораторная работа № 1\nНагрузочное тестирование приложения в Kubernetes", "Title")
paragraph(doc, "Цель работы: проверить, как приложение отвечает при разном числе пользователей, и найти нагрузку, при которой ответы становятся медленнее.")

doc.add_heading("1. Объект и условия испытания", 1)
paragraph(doc, "Я тестировал главную страницу auth-service из проекта Y3-S2-Kubernetes (коммит 35a202a8b3b84d959b6698dd5dbdeed7197b203a). Приложение работало в локальном Kubernetes K3s. Для запуска использовался Helm. У auth-service была одна реплика. Версии программ: K3s v1.37.0+k3s1, Helm v3.19.0, k6 v1.2.3.")
figure(doc, screenshots / "kubernetes-pods.png", "Рисунок 1. Работающие поды Kubernetes")
figure(doc, screenshots / "browser-auth.png", "Рисунок 2. Страница auth-service в браузере", 115)

doc.add_heading("2. Как проводился тест", 1)
paragraph(doc, "В k6 я написал простой сценарий. Он отправляет GET-запрос на главную страницу, проверяет код ответа 200 и ждёт одну секунду. Каждый тест длился 30 секунд. Сначала был базовый тест с 10 виртуальными пользователями (VU). Затем я проверил 10, 25, 50, 100, 200 и 400 VU.")
paragraph(doc, "RPS я посчитал так: число запросов разделил на 30 секунд. В самом k6 число немного другое, так как он учитывает фактическую длительность запуска. Время ответа p50, p90, p95 и p99 взято из http_req_duration. Процент ошибок взят из http_req_failed. Все исходные результаты лежат в папке results.")

doc.add_heading("3. Базовый тест", 1)
paragraph(doc, f"При 10 VU получилось {basic['requests']} запросов, то есть {basic['rps']:.2f} RPS. p50 составил {basic['p50']:.2f} мс, p95 составил {basic['p95']:.2f} мс, p99 составил {basic['p99']:.2f} мс. Ошибок не было.")
figure(doc, screenshots / "basic.png", "Рисунок 3. Сохранённый вывод базового теста в терминале")

doc.add_heading("4. Испытания при разной нагрузке", 1)
table(doc)
figure(doc, results / "latency_vs_load.png", "Рисунок 4. Изменение p95 при росте нагрузки")
figure(doc, results / "rps_vs_load.png", "Рисунок 5. Число запросов в секунду")
paragraph(doc, "До 100 VU число запросов в секунду росло вместе с нагрузкой. После 100 VU ответы стали заметно медленнее. В таблице и на графиках показаны данные тех же тестов, что и на снимках ниже.")
for number, (name, vus) in enumerate([("vu10", 10), ("vu25", 25), ("vu50", 50), ("vu100", 100), ("vu200", 200), ("vu400", 400)], 6):
    figure(doc, screenshots / f"{name}.png", f"Рисунок {number}. Сохранённый вывод k6 в терминале, {vus} VU")

doc.add_heading("5. Определение точки деградации", 1)
point = next(row for row in series if row["vus"] == 200)
previous = next(row for row in series if row["vus"] == 100)
paragraph(doc, f"Первое заметное ухудшение было при 200 VU. При 100 VU p95 равнялся {previous['p95']:.2f} мс, а при 200 VU вырос до {point['p95']:.2f} мс. Это рост примерно в {point['p95'] / previous['p95']:.2f} раза. Ошибок при этом не было. При 400 VU p95 составил {series[-1]['p95']:.2f} мс.")
paragraph(doc, "Сервер отвечал на все запросы, но некоторые ответы стали долгими. Возможно, запросам приходилось ждать или серверу не хватало ресурсов. По одному выводу k6 нельзя точно сказать, почему это произошло. Для этого нужно смотреть загрузку процессора, память и логи.")
paragraph(doc, "По методичке ухудшение можно заметить по росту p95 более чем в два раза, ошибкам выше 0,1 % или слабому росту RPS при увеличении числа VU вдвое.")

doc.add_heading("6. Ответы на контрольные вопросы", 1)
answers = [
    ("Что такое нагрузочное тестирование?", "Это проверка работы программы при большом числе одновременных запросов. Мы смотрим, успевает ли она отвечать и не появляются ли ошибки."),
    ("Что означают RPS, latency и перцентили?", "RPS показывает число запросов за секунду. Latency означает время ответа. Перцентиль показывает время, за которое успела завершиться заданная доля запросов."),
    ("Почему одного среднего недостаточно?", "Среднее не показывает, сколько было очень медленных ответов. Поэтому дополнительно смотрят p95 и p99."),
    ("Что означают p50, p95, p99?", "Это времена, быстрее которых завершились соответственно 50 %, 95 % и 99 % запросов. Например, p95 = 100 мс означает, что 95 % ответов пришли не позднее 100 мс."),
    ("Как работает k6 и что такое VU?", "k6 запускает написанный сценарий много раз. VU означает виртуального пользователя, который выполняет запросы по этому сценарию."),
    ("Как найти точку деградации?", "Постепенно увеличивать нагрузку и сравнивать задержку, RPS и ошибки. Если ответы резко замедляются или появляются ошибки, система начинает работать хуже."),
    ("Что такое thresholds?", "Это условия, по которым k6 автоматически оценивает тест. Например, можно потребовать, чтобы p95 был ниже заданного времени."),
    ("Как сформулировать требование к производительности?", "Нужно указать нагрузку и допустимые результаты. Например: при 100 VU p95 не больше 500 мс и ошибок меньше 1 % за 30 секунд."),
    ("Почему RPS может перестать расти?", "Сервер может достигнуть предела по процессору, памяти или другим ресурсам. Тогда новым запросам приходится ждать."),
    ("Как оптимизировать медленную систему?", "Сначала найти причину по метрикам и логам, затем ускорить проблемную часть программы или увеличить доступные ресурсы."),
]
for number, (question, answer) in enumerate(answers, 1):
    p = doc.add_paragraph()
    p.add_run(f"{number}. {question} ")
    p.add_run(answer)

doc.add_heading("7. Вывод", 1)
paragraph(doc, "Во всех тестах сервис ответил без ошибок. Но при 200 VU p95 вырос почти в четыре раза по сравнению со 100 VU. Значит, в этих условиях ухудшение работы впервые заметно при 200 VU.")
doc.add_heading("Использованные материалы", 1)
paragraph(doc, "Методические указания «ВП ЛР1.pdf», раздел «Задания для самостоятельного выполнения». Исходный проект: github.com/Wladisl4W/Y3-S2-Kubernetes. Правила оформления сверены с опубликованными рекомендациями МГУ и ННГУ; требования конкретной кафедры в задании не указаны.")

output = folder / "ЛР1_отчёт.docx"
doc.save(output)
print(output)
