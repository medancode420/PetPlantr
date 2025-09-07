// k6 load test for PetPlantr
import http from 'k6/http';
import { check } from 'k6';
import { Rate } from 'k6/metrics';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.3/index.js';
import encoding from 'k6/encoding';

// ---- Env & defaults ----
const BASE = __ENV.BASE_URL || 'http://localhost:8000';
const DURATION = __ENV.DURATION || '10m';
const BREED_RPS = Number(__ENV.BREED_RPS || '5');          // light traffic
const MESH_RPS  = Number(__ENV.MESH_RPS  || '1');          // heavier jobs
const READ_RPS  = Number(__ENV.READ_RPS  || '0.5');        // health probes

const BREED_P95_MS       = Number(__ENV.BREED_P95_MS || '500');
const MESH_ACCEPT_P95_MS = Number(__ENV.MESH_ACCEPT_P95_MS || '1500');
const MESH_BULK_RPS      = Number(__ENV.MESH_BULK_RPS || '0.2');

// ---- Tiny 1x1 PNG (base64), avoids external fixture files ----
const TINY_PNG_BASE64 =
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII=';
const IMG_BYTES = encoding.b64decode(TINY_PNG_BASE64, 'raw');

// ---- Custom metrics ----
const ladder202 = new Rate('ladder_202');           // % of mesh responses with X-Queue-Ladder
const meshAccepted202 = new Rate('mesh_accepted');  // % of mesh responses that returned 202
const breedOk = new Rate('breed_ok');               // % of breed requests acceptable (200/202)

// ---- Scenarios & thresholds ----
export const options = {
  discardResponseBodies: true,
  summaryTimeUnit: 'ms',
  scenarios: {
    breed_ui: {
      executor: 'constant-arrival-rate',
      exec: 'breed_ui',
      rate: BREED_RPS,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: Number(__ENV.BREED_VUS || '20'),
      maxVUs: Number(__ENV.BREED_MAX_VUS || '100'),
    },
    mesh_ui: {
      executor: 'constant-arrival-rate',
      exec: 'mesh_ui',
      rate: MESH_RPS,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: Number(__ENV.MESH_VUS || '20'),
      maxVUs: Number(__ENV.MESH_MAX_VUS || '200'),
    },
    mesh_bulk: {
      executor: 'constant-arrival-rate',
      exec: 'mesh_bulk',
      rate: MESH_BULK_RPS,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: Number(__ENV.MESH_BULK_VUS || '10'),
      maxVUs: Number(__ENV.MESH_BULK_MAX_VUS || '50'),
    },
    health_read: {
      executor: 'constant-arrival-rate',
      exec: 'health_read',
      rate: READ_RPS,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: 2,
      maxVUs: 10,
    },
  },
  thresholds: {
    'http_req_failed{scenario:breed_ui}': ['rate<0.01'],
    'http_req_duration{scenario:breed_ui}': [`p(95)<${BREED_P95_MS}`],
    'http_req_failed{scenario:mesh_ui}': ['rate<0.03'],
    'http_req_duration{scenario:mesh_ui}': [`p(95)<${MESH_ACCEPT_P95_MS}`], // acceptance/202 path
    'http_req_failed{scenario:mesh_bulk}': ['rate<0.03'],
    'http_req_duration{scenario:mesh_bulk}': [`p(95)<${MESH_ACCEPT_P95_MS}`],
    'checks{scenario:health_read}': ['rate>0.99'],
    'ladder_202{scenario:mesh_ui}': ['rate<0.10'],      // queue ladder should be <10% of mesh traffic
    'mesh_accepted{scenario:mesh_ui}': ['rate>0.80'],   // expect most mesh requests return 202 fast
    'breed_ok{scenario:breed_ui}': ['rate>0.99'],
  },
  summaryTrendStats: ['avg', 'p(95)', 'p(99)', 'min', 'max'],
};

// ---- Scenario functions ----
export function breed_ui() {
  const data = { image: http.file(IMG_BYTES, 'tiny.png', 'image/png') };
  const params = {
    headers: { 'X-Client': 'ui' },
    timeout: '30s',
  };
  const res = http.post(`${BASE}/api/v1/breed/detect`, data, params);
  const ok = res.status === 200 || res.status === 202;
  breedOk.add(ok);
  check(res, { 'breed accepted (200/202)': () => ok });
}

export function mesh_ui() {
  const data = { image: http.file(IMG_BYTES, 'tiny.png', 'image/png') };
  const params = {
    headers: { 'X-Client': 'ui' },
    timeout: '45s',
  };
  const res = http.post(`${BASE}/api/v1/mesh/generate`, data, params);
  const ok = res.status === 200 || res.status === 202;
  meshAccepted202.add(res.status === 202);
  ladder202.add(!!res.headers['X-Queue-Ladder']);
  check(res, { 'mesh accepted (200/202)': () => ok });
}

export function mesh_bulk() {
  const data = { image: http.file(IMG_BYTES, 'tiny.png', 'image/png') };
  const params = {
    headers: { 'X-Client': 'bulk' },
    timeout: '60s',
  };
  const res = http.post(`${BASE}/api/v1/mesh/generate`, data, params);
  const ok = res.status === 200 || res.status === 202;
  meshAccepted202.add(res.status === 202);
  ladder202.add(!!res.headers['X-Queue-Ladder']);
  check(res, { 'mesh_bulk accepted (200/202)': () => ok });
}

export function health_read() {
  const res = http.get(`${BASE}/api/v1/health`, { timeout: '10s' });
  check(res, {
    'health 200': (r) => r.status === 200,
    'pipeline real': (r) => (r.json('pipeline') || '') === 'real',
  });
}

// ---- Summaries to disk (artifacts) ----
export function handleSummary(data) {
  return {
    'reports/k6-summary.json': JSON.stringify(data, null, 2),
    'reports/k6-summary.txt': textSummary(data, { indent: ' ', enableColors: false }),
  };
}
