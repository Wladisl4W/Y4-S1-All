import http from 'k6/http';
import { check } from 'k6';
import exec from 'k6/execution';

const base = __ENV.TARGET_URL || 'http://127.0.0.1:30085';
const mode = __ENV.MODE || 'off';
const keys = Number(__ENV.KEY_COUNT || 10);

export const options = {
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
  scenarios: {
    cache: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.RATE || 10),
      timeUnit: '1s',
      duration: __ENV.DURATION || '60s',
      preAllocatedVUs: 100,
      maxVUs: 600,
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

export default function () {
  const id = (exec.scenario.iterationInTest % keys) + 1;
  const response = http.get(`${base}/data/${id}?cache=${mode}`, { timeout: '10s' });
  check(response, { 'status is 200': (r) => r.status === 200 });
}
