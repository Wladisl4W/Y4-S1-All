"""Apply updated evidence to the student's existing ODT without regenerating it."""

from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile

from lxml import etree


folder = Path(__file__).parent
source = folder / 'ЛР2_отчёт.odt'
temporary = source.with_suffix('.odt.tmp')
ns = {
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
    'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
    'xlink': 'http://www.w3.org/1999/xlink',
    'manifest': 'urn:oasis:names:tc:opendocument:xmlns:manifest:1.0',
}
href = '{%s}href' % ns['xlink']


def caption_text(node):
    return ''.join(node.itertext()).strip()


with ZipFile(source) as archive:
    content = etree.fromstring(archive.read('content.xml'))
    manifest = etree.fromstring(archive.read('META-INF/manifest.xml'))
    paragraphs = content.xpath('//text:p', namespaces=ns)
    figures = {caption_text(p): p for p in paragraphs if caption_text(p).startswith('Рисунок ')}
    replacements = {}
    first = next(p for title, p in figures.items() if title.startswith('Рисунок 1.'))
    first_image = first.getprevious().xpath('.//draw:image', namespaces=ns)[0]
    replacements[first_image.get(href)] = (folder / 'results/screenshots' / 'monitoring-pods.png').read_bytes()
    for child in first.iter():
        if child.text and child.text.startswith('Рисунок 1.'):
            child.text = 'Рисунок 1. Просмотр сохранённого списка подов мониторинга'
            break
    for number, vus in enumerate((10, 50, 200), 4):
        caption = next(p for title, p in figures.items() if title.startswith(f'Рисунок {number}.'))
        picture = caption.getprevious().xpath('.//draw:image', namespaces=ns)[0]
        replacements[picture.get(href)] = (folder / 'results/screenshots' / f'vu{vus}.png').read_bytes()
        # A caption is one text node in the current, student-edited ODT.
        for child in caption.iter():
            if child.text and child.text.startswith(f'Рисунок {number}.'):
                child.text = f'Рисунок {number}. Просмотр сохранённого вывода k6 для {vus} VU'
                break

    seven = next(p for title, p in figures.items() if 'Изменение p95 при росте нагрузки' in title)
    if not any('Изменение RPS во времени' in title for title in figures):
        parent = seven.getparent()
        index = parent.index(seven.getprevious())
        explanation = deepcopy(seven)
        explanation.set('{%s}style-name' % ns['text'], 'Standard')
        for child in explanation.iter():
            if child.text and 'Рисунок 7.' in child.text:
                child.text = ('По сохранённым ответам Prometheus на запрос '
                              'sum(rate(http_requests_total{namespace="vp-lr2",route="index"}[15s])) '
                              'построен график RPS во времени. Это не снимок веб-интерфейса: '
                              'локальный кластер сейчас остановлен.')
                break
        parent.insert(index, explanation)
        new_picture = deepcopy(seven.getprevious())
        new_image = new_picture.xpath('.//draw:image', namespaces=ns)[0]
        new_path = 'Pictures/prometheus-rps-time.png'
        new_image.set(href, new_path)
        parent.insert(index + 1, new_picture)
        new_caption = deepcopy(seven)
        for child in new_caption.iter():
            if child.text and child.text.startswith('Рисунок 7.'):
                child.text = 'Рисунок 7. Изменение RPS во времени по сохранённым ответам Prometheus'
                break
        parent.insert(index + 2, new_caption)
        replacements[new_path] = (folder / 'results/prometheus-rps-time.png').read_bytes()
        entry = etree.SubElement(manifest, '{%s}file-entry' % ns['manifest'])
        entry.set('{%s}full-path' % ns['manifest'], new_path)
        entry.set('{%s}media-type' % ns['manifest'], 'image/png')

    for paragraph in content.xpath('//text:p', namespaces=ns):
        if caption_text(paragraph).startswith('Сохранённые ответы Prometheus на запрос'):
            paragraph.set('{%s}style-name' % ns['text'], 'Standard')
            for child in paragraph.iter():
                if child.text and child.text.startswith('Сохранённые ответы Prometheus на запрос'):
                    child.text = ('По сохранённым ответам Prometheus на запрос '
                                  'sum(rate(http_requests_total{namespace="vp-lr2",route="index"}[15s])) '
                                  'построен график RPS во времени. Это не снимок веб-интерфейса: '
                                  'локальный кластер сейчас остановлен.')
                    break

    table_ns = {'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
                'text': ns['text']}
    for row in content.xpath('//table:table-row', namespaces=table_ns):
        if 'http_request_duration_seconds_bucket' in ''.join(row.itertext()):
            cells = row.xpath('./table:table-cell', namespaces=table_ns)
            if cells:
                for paragraph in cells[-1].xpath('.//text:p', namespaces=table_ns):
                    for child in paragraph.iter():
                        if child.text == 'сек':
                            child.text = 'запрос'

    figure_numbers = {
        'Изменение RPS во времени': 7,
        'Изменение p95 при росте нагрузки': 8,
        'Средние CPU и память': 9,
        'Пропускная способность по данным k6': 10,
    }
    for paragraph in content.xpath('//text:p', namespaces=ns):
        title = caption_text(paragraph)
        for phrase, number in figure_numbers.items():
            if phrase in title and title.startswith('Рисунок '):
                for child in paragraph.iter():
                    if child.text and child.text.startswith('Рисунок '):
                        child.text = 'Рисунок ' + str(number) + '.' + child.text.split('.', 1)[1]
                        break

    with ZipFile(temporary, 'w') as output:
        for item in archive.infolist():
            value = archive.read(item.filename)
            if item.filename == 'content.xml':
                value = etree.tostring(content, encoding='UTF-8', xml_declaration=True)
            elif item.filename == 'META-INF/manifest.xml':
                value = etree.tostring(manifest, encoding='UTF-8', xml_declaration=True)
            elif item.filename in replacements:
                value = replacements.pop(item.filename)
            output.writestr(item, value)
        for path, value in replacements.items():
            output.writestr(path, value)

temporary.replace(source)
