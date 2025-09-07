import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const API_BASE = __ENV.API_BASE || 'http://localhost:8000';
const IMAGE_PATH = __ENV.K6_IMAGE || 'test_dog.jpg';
let IMG_DATA;
try {
  IMG_DATA = open(IMAGE_PATH, 'b');
} catch (e) {
  IMG_DATA = null; // fallback to read-only if image missing
}

export const options = {
  scenarios: {
    default: {
      executor: 'constant-vus',
      vus: Number(__ENV.VUS) || 10,
      duration: __ENV.DURATION || '2m',
      gracefulStop: '30s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.02'],
    'http_req_duration{group:breed}': ['p(95)<800'],
    'http_req_duration{group:mesh}': ['p(95)<3500'],
    'http_req_duration{group:read}': ['p(95)<300'],
  },
};

const successRate = new Rate('petplantr_success_rate');

function randBetween(min, max) {
  return Math.random() * (max - min) + min;
}

function doBreed() {
  group('breed', () => {
    if (!IMG_DATA) {
      const r = http.get(`${API_BASE}/api/v1/health`);
      check(r, { '200': (res) => res.status === 200 });
      successRate.add(r.status === 200);
      return;
    }
    const fd = {
      file: http.file(IMG_DATA, 'test_dog.jpg', 'image/jpeg'),
      use_tta: 'true',
      confidence_threshold: '0.8',
    };
    const r = http.post(`${API_BASE}/api/v1/breed/detect`, fd);
    check(r, { '200': (res) => res.status === 200 });
    successRate.add(r.status === 200);
  });
}

function doMesh() {
  group('mesh', () => {
    const payload = {
      image_url: 'https://via.placeholder.com/256.png',
      quality_level: 'standard',
      include_breed_detection: 'true',
    };
    const r = http.post(`${API_BASE}/api/v1/generate-enhanced-3d-simple`, payload);
    check(r, { '200': (res) => res.status === 200 });
    successRate.add(r.status === 200);
  });
}

function doRead() {
  group('read', () => {
    const r = http.get(`${API_BASE}/api/v1/health`);
    check(r, { '200': (res) => res.status === 200 });
    successRate.add(r.status === 200);
  });
}

export default function () {
  const p = Math.random();
  if (p < 0.7) doBreed();
  else if (p < 0.9) doMesh();
  else doRead();
  sleep(randBetween(0.1, 0.3));
}
