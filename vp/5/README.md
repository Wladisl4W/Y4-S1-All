# ЛР5: Redis и Cache-Aside

В папке находятся исходный код приложения, манифесты K3s, сценарий k6, dashboard Grafana, исходные результаты опытов и отчёт. `ВП ЛР5.pdf` - исходное задание.

## Запуск

Нужен прежний K3s. После запуска и появления узла в состоянии `Ready` выполнить из `/home/wladisl4w/uni/4`:

```bash
export KUBECONFIG="$HOME/.kube/config"
k3s kubectl create namespace vp-lr5 --dry-run=client -o yaml | k3s kubectl apply -f -
k3s kubectl apply -f vp/5/redis.yaml
k3s kubectl -n vp-lr5 create configmap cache-app-source \
  --from-file=app.py=vp/5/app.py \
  --from-file=requirements.txt=vp/5/requirements.txt \
  --dry-run=client -o yaml | k3s kubectl apply -f -
k3s kubectl apply -f vp/5/cache-app.yaml -f vp/5/service-monitor.yaml
k3s kubectl -n vp-lr5 rollout status deployment/redis
k3s kubectl -n vp-lr5 rollout status deployment/cache-app
```

Контейнер приложения использует официальный `python:3.12-slim`. Пакеты скачаны с официального PyPI в `wheels/` и устанавливаются из локальной папки, подключённой к Pod через `hostPath`. Это нужно для воспроизведения на данном одноузловом K3s: прямой выход контейнера к PyPI не работал. `Dockerfile` показывает обычный способ сборки того же приложения там, где доступен сборщик контейнеров. Путь `hostPath` в `cache-app.yaml` относится к этому компьютеру; на другом узле его нужно заменить на путь к wheel-файлам.

Проверка:

```bash
k3s kubectl -n vp-lr5 get pods
k3s kubectl -n vp-lr5 exec deployment/redis -- redis-cli PING
curl --noproxy '*' 'http://АДРЕС_УЗЛА:30085/data/1?cache=off'
curl --noproxy '*' 'http://АДРЕС_УЗЛА:30085/data/1?cache=on'
curl --noproxy '*' 'http://АДРЕС_УЗЛА:30085/metrics'
```

При первой проверке `cache=on` ответ помечен `miss`, при следующей до истечения TTL - `hit`.

## Эксперимент

Адрес узла определяется через `k3s kubectl get nodes -o wide`. Для повторения всех опытов:

```bash
TARGET_URL=http://АДРЕС_УЗЛА:30085 python3 vp/5/run_experiments.py
```

Один сценарий k6 `test-cache.js` используется при каждом запуске. Исходные выводы и JSON k6, ответы Prometheus и сводка сохранены в `results/`. Скрипт очищает только Redis в namespace `vp-lr5` перед каждой серией. При сравнении пропускной способности в режиме `on` он заранее заполняет десять ключей. Прогоны по разнообразию ключей и TTL начинаются с пустого кэша. Сводка сохраняет фактический адрес, интервалы времени и счётчики до и после каждого запуска. Если счётчики уменьшаются из-за перезапуска Pod, результат не принимается.

В `results/invalid-first-attempt/` и `results/invalid-probes-attempt/` сохранены пробные серии, которые не использовали в отчёте: liveness probe перезапускала однопроцессное приложение при перегрузке. Liveness probe убрана, а readiness probe на `/health` сохранена с увеличенным порогом отказов; после этого вся серия была начата заново. Сценарий с 1000 ключами длится 120 секунд при 10 запросах/с, чтобы каждый ключ мог быть запрошен хотя бы раз.

В `results/invalid-interrupted-ttl120/` лежит первый, прерванный опыт TTL 120 секунд: фактическая интенсивность упала до 1 RPS, поэтому его данные исключены из итоговой сводки. Опыт повторён отдельно после восстановления K3s.

## Grafana и отчёт

После запуска Grafana через `k3s kubectl -n monitoring port-forward svc/prometheus-grafana 13000:80`:

```bash
python3 vp/5/build_dashboard.py
python3 vp/5/grafana_api.py source
python3 vp/5/grafana_api.py install
python3 vp/5/grafana_api.py verify
python3 vp/5/grafana_api.py export
```

Пароль Grafana читается из текущего Kubernetes Secret только во время запроса и не сохраняется в файлы. Для отчёта используются настоящие снимки Ptyxis и Grafana, сохранённые в `screenshots/`. Терминальные снимки показывают команду `cat`, читающую сохранённый вывод уже завершённого k6, а не новый запуск теста.

График p95 и отчёт можно пересоздать после завершения всех опытов:

```bash
python3 vp/5/build_chart.py
python3 vp/5/build_report.py
```

Команда создания терминальных снимков: `python3 vp/5/capture_terminal.py`. Для неё нужны установленные Ptyxis, Xvfb, Openbox и FFmpeg. Снимки Grafana относятся к сохранённым временным диапазонам итоговой серии; они сделаны непосредственно в работающем интерфейсе.
