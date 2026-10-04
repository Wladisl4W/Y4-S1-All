# Лабораторная работа 1

Нагрузочное тестирование главной страницы `auth-service` из
[Y3-S2-Kubernetes](https://github.com/Wladisl4W/Y3-S2-Kubernetes),
коммит `35a202a8b3b84d959b6698dd5dbdeed7197b203a`.

## Файлы

- `test.js` — сценарий k6: GET главной страницы, проверка HTTP 200 и пауза 1 с между итерациями.
- `run_tests.sh` — базовый тест и серия от 10 до 200 VU, затем при необходимости 400 и 800 VU; каждый по 30 с.
- `analyze.py` — таблица метрик, поиск первой точки деградации и графики.
- `make_report.py` — создание Word-отчёта из результатов.
- `capture_screenshots.py` — получение снимков окон Ptyxis с сохранённым выводом тестов (нужны Xvfb, Openbox, Ptyxis и ffmpeg; дисплей `:99`).
- `target-chart/` — копия Helm chart прошлого семестра с исходными файлами трёх сервисов.
- `results/` — исходный вывод k6 (`.txt`), машиночитаемые сводки (`.json`), графики и снимки экрана.
- `ЛР1_отчёт.docx` — готовый отчёт с таблицей, графиками, снимками и ответами на вопросы.

## Развёртывание

Нужны K3s, Helm 3 и k6. Сервисы запускаются из исходных файлов старого
репозитория через образ `python:3.11-slim`: отдельная сборка Docker-образов
для этой лабораторной не нужна. В `target-chart/values-lab1.yaml` зафиксированы
одна реплика каждого сервиса и отключённый Ingress.

Если инструменты ещё не установлены, можно повторить использованные версии:

```bash
curl -L -o /tmp/k3s 'https://github.com/k3s-io/k3s/releases/download/v1.37.0%2Bk3s1/k3s'
sudo install -m 755 /tmp/k3s /usr/local/bin/k3s
curl -L -o /tmp/helm.tar.gz https://get.helm.sh/helm-v3.19.0-linux-amd64.tar.gz
tar -xzf /tmp/helm.tar.gz -C /tmp
install -m 755 /tmp/linux-amd64/helm ~/.local/bin/helm
curl -L -o /tmp/k6.tar.gz https://github.com/grafana/k6/releases/download/v1.2.3/k6-v1.2.3-linux-amd64.tar.gz
tar -xzf /tmp/k6.tar.gz -C /tmp
install -m 755 /tmp/k6-v1.2.3-linux-amd64/k6 ~/.local/bin/k6
```

Запустить локальный кластер и приложение из папки ЛР1:

```bash
sudo systemd-run --unit=vp-lr1-k3s --property=Restart=on-failure \
  /usr/local/bin/k3s server --disable=traefik --disable=servicelb
mkdir -p ~/.kube
sudo install -m 600 -o "$USER" -g "$USER" \
  /etc/rancher/k3s/k3s.yaml ~/.kube/config
helm upgrade --install vp-lr1 target-chart \
  -f target-chart/values-lab1.yaml --namespace vp-lr1 --create-namespace
KUBECONFIG=~/.kube/config k3s kubectl -n vp-lr1 rollout status deployment/auth-service
curl -i http://127.0.0.1:30080/
```

Для сравнения нагрузки условия должны оставаться одинаковыми: тот же стенд,
число реплик и адрес сервиса. Если NodePort недоступен на `127.0.0.1`, используйте
адрес узла Kubernetes в `TARGET_URL`.

## Запуск и анализ

Из папки этой лабораторной:

```bash
TARGET_URL=http://127.0.0.1:30080/ bash run_tests.sh
python3 analyze.py
python3 make_report.py
```

RPS считается как `http_reqs / 30 с`. Число в консоли k6 может слегка отличаться,
потому что учитывает фактическую длительность прогона. Для точки деградации проверяются условия
методички: рост p95 более чем в 2 раза относительно прошлого теста, ошибки
выше 0,1%, либо прирост RPS меньше 10% при удвоении числа VU. Последний
критерий применяется только к парам с точным удвоением нагрузки.
