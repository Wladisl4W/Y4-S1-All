import http from 'k6/http';
import { check, sleep } from 'k6';

// The runner calls this scenario once for each required VU level.
export const options = {
  vus: Number(__ENV.VUS || 10),
  duration: __ENV.DURATION || '90s',
  summaryTrendStats: ['avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'min', 'max'],
};

export default function () {
  const response = http.get(__ENV.TARGET_URL || 'http://127.0.0.1:30082/');
  check(response, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
