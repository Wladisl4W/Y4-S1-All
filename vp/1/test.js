import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: Number(__ENV.VUS || 10),
  duration: __ENV.DURATION || '30s',
  summaryTrendStats: ['avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'min', 'max'],
};

export default function () {
  const response = http.get(__ENV.TARGET_URL || 'http://127.0.0.1:30080/');
  check(response, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
