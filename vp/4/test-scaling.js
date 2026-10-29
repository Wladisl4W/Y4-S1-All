import http from 'k6/http';
import { check } from 'k6';

const target = __ENV.TARGET_URL || 'http://127.0.0.1:30083/work?iterations=20000';

export const options = {
  scenarios: {
    scaling: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.RATE || 10),
      timeUnit: '1s',
      duration: __ENV.DURATION || '60s',
      preAllocatedVUs: 50,
      maxVUs: 400,
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

export default function () {
  const response = http.get(target);
  check(response, { 'status is 200': (r) => r.status === 200 });
}
