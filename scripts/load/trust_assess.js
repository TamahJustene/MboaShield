/**
 * MboaShield k6 scenario (T6) - trust assess + health.
 *
 * Usage:
 *   k6 run -e BASE_URL=http://127.0.0.1:8000 scripts/load/trust_assess.js
 */
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 10,
  duration: "60s",
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<3000"],
  },
};

const BASE = __ENV.BASE_URL || "http://127.0.0.1:8000";

export default function () {
  const health = http.get(`${BASE}/health`);
  check(health, { "health 200": (r) => r.status === 200 });

  const assess = http.post(
    `${BASE}/api/v1/trust/assess`,
    JSON.stringify({
      object_type: "text",
      text: "Official grant - click here immediately",
      lang: "en",
      persist: true,
    }),
    { headers: { "Content-Type": "application/json" } }
  );
  check(assess, {
    "assess 200": (r) => r.status === 200,
    "assess has score": (r) => {
      try {
        return r.json("score") !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  sleep(1);
}
