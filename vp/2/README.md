# Лабораторная работа 2: Prometheus

Объект исследования: `auth-service` из проекта прошлого семестра. Здесь лежит
отдельная копия Helm chart; файлы ЛР1 не изменялись.

## Подготовка

Нужны K3s, Helm, k6 и Python с matplotlib. Команды выполнять из этой папки.
K3s должен быть запущен; для kubectl использовать
`KUBECONFIG=$HOME/.kube/config k3s kubectl`.

```bash
helm upgrade --install vp-lr2 ./target-chart -n vp-lr2 --create-namespace -f target-chart/values-lab2.yaml
helm upgrade --install prometheus ./vendor/kube-prometheus-stack-89.2.0.tgz -n monitoring --create-namespace -f prometheus-values.yaml
KUBECONFIG=$HOME/.kube/config k3s kubectl apply -f service-monitor.yaml
KUBECONFIG=$HOME/.kube/config k3s kubectl -n monitoring get pods
KUBECONFIG=$HOME/.kube/config k3s kubectl -n vp-lr2 get pods
KUBECONFIG=$HOME/.kube/config k3s kubectl -n monitoring port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090
```

Последняя команда занимает терминал. После неё Prometheus доступен по
`http://127.0.0.1:9090/`. `auth-service` доступен по
`http://127.0.0.1:30081/`, метрики по `/metrics`. Проверка:

```bash
curl -fsS http://127.0.0.1:30081/metrics | grep http_requests_total
curl -G 'http://127.0.0.1:9090/api/v1/query' --data-urlencode 'query=up{namespace="vp-lr2",service="auth-service"}'
python3 run_tests.py
python3 analyze.py
```

`run_tests.py` запускает три теста по 30 секунд: 10, 50 и 200 VU. Между ними
выдерживается пауза 40 секунд. Исходный вывод k6 находится в `results/vu*.txt`,
его JSON в `results/vu*.json`, ответы Prometheus и время прогонов в
`results/vu*.prometheus.json`. `analyze.py` строит таблицу `results/summary.json`
и графики из этих файлов. При повторе тестов предыдущие файлы с теми же именами
будут перезаписаны.

На этой машине DNS внутри K3s сначала возвращал неправильный адрес для PyPI.
Для запуска я настроил CoreDNS на DNS-сервер `100.64.0.1` и добавил `ndots: 1`
в deployment-файлы сервисов. Настройка CoreDNS была сделана в работающем
кластере и после переустановки K3s может понадобиться снова. Для проверки:

```bash
KUBECONFIG=$HOME/.kube/config k3s kubectl -n kube-system get configmap coredns -o yaml
```

CPU в отчёте показан в процентах от **одного логического ядра**, а память в МиБ.
CPU может быть больше 100%, если процесс использует больше одного ядра.
Prometheus p95 относится ко времени обработки внутри Flask и вычисляется по
бакетам гистограммы за 40 секунд; k6 p95 относится к полному времени ответа
клиенту за 30 секунд теста. Поэтому эти значения не обязаны совпадать.
