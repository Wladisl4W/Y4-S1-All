# Четыре лабораторные по пособию Protégé

Тема: дипломное приложение для тренировки интонации. Нумерация 1–4 соответствует лабораторным работам PDF `files/20200802_2.pdf` (страницы 6, 34, 41 и 48). Задания про смартфоны, ноутбуки и холодильники адаптированы к предметной области приложения. Данные о паттернах и настройках сверены с исходным кодом `/home/wladisl4w/uni/diplom` и `docs/warmups.md`. Результаты пения и личная история не импортировались.

| Папка | Работа | Что открыть |
| --- | --- | --- |
| `1` | RDF и OWL | `ontology.ttl`, `results.txt`, `ЛР1_отчёт.odt` |
| `2` | Defined classes | `ontology.ttl`, `results.txt`, `ЛР2_отчёт.odt` |
| `3` | SPARQL | `ontology.ttl`, `queries/`, `results.txt`, `ЛР3_отчёт.odt` |
| `4` | SWRL | `ontology.ttl`, `rules.swrl`, `results.txt`, `ЛР4_отчёт.odt` |

В Protégé открыть `File → Open` и выбрать нужный `ontology.ttl`. Для второй работы запустить reasoner и посмотреть inferred individuals пяти defined classes. Для третьей включить `Window → Tabs → SPARQL Query` и вставлять тексты `.rq`. Для четвёртой необходим SWRL-совместимый движок: в текущем окружении проверены структура правил и их условия отдельным скриптом, но сам SWRL-вывод не выполнялся.

Локально использованы Python 3, `rdflib` и `owlrl`. Проверки запускаются из корня проекта: `python3 ii/2/check_defined.py`, `python3 ii/3/run_queries.py`, `python3 ii/4/check_rules.py`. Если пакеты не установлены, можно использовать `uv run --no-project --offline --with rdflib --with owlrl python3 ...` при наличии пакетов в кэше.
