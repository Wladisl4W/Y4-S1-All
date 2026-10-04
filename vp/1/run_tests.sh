#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
mkdir -p results

TARGET_URL="${TARGET_URL:-http://127.0.0.1:30080/}"
export TARGET_URL

run_test() {
    local name="$1"
    local vus="$2"
    echo "Running $name with $vus VU"
    VUS="$vus" DURATION=30s k6 run --summary-export "results/${name}.json" test.js 2>&1 | tee "results/${name}.txt"
}

run_test basic 10
for vus in 10 25 50 100 200; do
    run_test "vu${vus}" "$vus"
done

python3 analyze.py
if python3 -c 'import json; exit(json.load(open("results/summary.json"))["degradation"] is None)'; then
    exit 0
fi

for vus in 400 800; do
    run_test "vu${vus}" "$vus"
    python3 analyze.py
    if python3 -c 'import json; exit(json.load(open("results/summary.json"))["degradation"] is None)'; then
        break
    fi
done
