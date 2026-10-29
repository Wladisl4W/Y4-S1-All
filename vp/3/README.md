# ЛР3: Grafana и анализ нагрузки

Здесь находятся приложение для ЛР3, dashboard Grafana, исходные результаты пяти новых прогонов и отчёт. Данные и снимки получены с работающих K3s, k6, Prometheus, Grafana и терминала Ptyxis. Снимки не дорисованы. Изображения терминала показывают команду просмотра сохранённого вывода после завершения теста.

## Что получилось

- Namespace приложения: `vp-lr3`, NodePort auth-service: `30082`.
- Monitoring: `kube-prometheus-stack`, Grafana и Prometheus в namespace `monitoring`.
- Dashboard: `High-load Application`, UID `vp-lr3-high-load`, семь панелей и переменные `namespace` и `pod`.
- Alert: `Error Rate > 1%`, оценка раз в 1 минуту, выдержка 2 минуты. Во время теста ошибок 5xx не было, поэтому состояние Normal.
- Нагрузка: 10, 25, 50, 100 и 200 VU по 90 секунд. Результаты: `results/summary.json`, исходные k6 и ответы Prometheus в `results/`.
- Повторный импорт `high-load-dashboard.json` проверен в веб-интерфейсе как отдельная копия с UID `vp-lr3-import-check`.

## Воспроизведение

Работать из этой папки. Требуются `helm`, `k6`, Python 3 и доступ к образам контейнеров. Если прежний K3s остановлен, запустите `sudo k3s server` в отдельном терминале и дождитесь состояния Ready у узла. В этом окружении для Python-пакетов контейнеров используется зеркало Aliyun, потому что прямой доступ к PyPI не проходил. Пароль Grafana хранится только в Kubernetes Secret и не записывается в проект.

```bash
export KUBECONFIG="$HOME/.kube/config"
helm upgrade --install vp-lr3 ./target-chart -n vp-lr3 --create-namespace -f target-chart/values-lab3.yaml
helm upgrade --install prometheus ./vendor/kube-prometheus-stack-89.2.0.tgz -n monitoring --create-namespace -f prometheus-values.yaml
k3s kubectl apply -f service-monitor.yaml
k3s kubectl get pods -n monitoring
k3s kubectl get svc -n monitoring prometheus-grafana
```

В двух отдельных терминалах открыть локальные порты:

```bash
k3s kubectl -n monitoring port-forward svc/prometheus-grafana 3000:80
k3s kubectl -n monitoring port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090
```

Локальная сеть этой машины при включённом VPN направляла адреса Kubernetes Service и DNS не туда. Поэтому в `prometheus-values.yaml` URL источника данных Grafana указывает на **текущий IP пода Prometheus** (`10.42.0.122`). После пересоздания пода этот адрес может измениться. Перед обновлением Helm values проверьте новый адрес и замените URL:

```bash
k3s kubectl -n monitoring get pod prometheus-prometheus-kube-prometheus-prometheus-0 -o wide
```

Затем проверить источник Prometheus кнопкой Test в Grafana или командой `python3 grafana_api.py source`. Этот локальный обход сетевой проблемы не нужен в кластере с нормально работающим Service DNS.

Для загрузки dashboard и правила после запуска port-forward:

```bash
python3 grafana_api.py install
python3 grafana_api.py verify
python3 configure_alert.py
```

Для нового эксперимента:

```bash
python3 run_tests.py
```

`run_tests.py` пропускает уровни, для которых уже есть строки в `results/summary.json`. Чтобы провести полностью новый опыт, сначала перенесите текущую папку `results/` в архив и создайте пустую. Запуск k6 внутри скрипта: `k6 run --summary-export results/vuN.json test-stages.js` с переменными `VUS=N`, `DURATION=90s` и `TARGET_URL=http://127.0.0.1:30082/`. Prometheus опрашивается за последние 30 секунд каждого этапа. Сценарий выполняет один GET и паузу 1 секунду.

Отчёт строится из `results/summary.json`, `high-load-dashboard.json` и настоящих снимков в `screenshots/`:

```bash
python3 build_report.py
```

Снимки терминала можно переснять командой `python3 capture_terminal.py` при установленных Xvfb, Openbox, Ptyxis и ffmpeg. Скрипт действительно открывает Ptyxis и вводит команды в его окно; курсор терминала скрыт настройкой приглашения. Снимки Grafana сделаны во время работающего теста, проверки источника, просмотра правила и импорта.

## Важное ограничение результата

На 100 VU резко вырос p95 k6, но серверный p95 оставался ниже, RPS продолжил расти до 200 VU, ошибок не было. Поэтому в отчёте отмечено ухудшение клиентской задержки, а не доказанное насыщение auth-service. Аннотация Grafana отмечает начало этапа 100 VU.
