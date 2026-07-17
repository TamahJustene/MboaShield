"""
MboaShield Locust load scenarios (T6).

Usage:
  locust -f scripts/load/locustfile.py --host https://YOUR_HOST
  # or: locust -f scripts/load/locustfile.py --host http://127.0.0.1:8000 --headless -u 20 -r 5 -t 2m
"""

from __future__ import annotations

from locust import HttpUser, between, task


class MboaShieldUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(3)
    def health(self) -> None:
        self.client.get("/health")

    @task(5)
    def trust_assess_text(self) -> None:
        self.client.post(
            "/api/v1/trust/assess",
            json={
                "object_type": "text",
                "text": "URGENT: send mobile money to verify your account now",
                "lang": "en",
                "persist": True,
            },
            headers={"Content-Type": "application/json"},
            name="/api/v1/trust/assess [text]",
        )

    @task(1)
    def program(self) -> None:
        self.client.get("/api/v1/program")

    @task(1)
    def verify_announcement_path(self) -> None:
        # Public verify UI/API warm path; 404 is acceptable if no id - still exercises stack.
        self.client.get("/api/v1/announcements", name="/api/v1/announcements [list]")
