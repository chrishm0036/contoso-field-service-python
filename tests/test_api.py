from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess

import pytest
from fastapi.testclient import TestClient

from app import main
from app.models import CreateJobRequest
from app.service import JobService

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client(monkeypatch):
    current_time = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(main, "service", JobService.with_demo_data(now_provider=lambda: current_time))
    with TestClient(main.app) as client:
        yield client


def test_dashboard_health_and_docs(client):
    page = client.get("/")
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    assert "Contoso Field Service" in page.text
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200
    for asset in ("app.js", "styles.css"):
        assert client.get("/static/" + asset).status_code == 200


def test_seeded_jobs_and_detail(client):
    response = client.get("/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 6
    assert all(job["status"] == "open" for job in jobs)
    assert all(job["sla_status"] in {"within_sla", "breached"} for job in jobs)
    assert all(isinstance(job["sla_remaining_seconds"], int) for job in jobs)
    assert client.get("/jobs/1").json() == jobs[0]
    assert client.get("/jobs/999").status_code == 404
    assert client.get("/jobs/not-an-id").status_code == 422


def test_create_job(client):
    response = client.post("/jobs", json={
        "customer_name": "Test customer", "description": "New incident",
        "priority": "high", "location": "Madrid", "technician": "Elena",
    })
    assert response.status_code == 201
    job = response.json()
    assert job["id"] == 7
    assert job["status"] == "open"
    assert job["sla_status"] == "within_sla"
    assert job["sla_remaining_seconds"] == 4 * 60 * 60
    assert client.get("/jobs/7").json() == job
    assert len(client.get("/jobs").json()) == 7


def test_job_detail_reports_breached_sla(monkeypatch):
    current_time = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    service = JobService(now_provider=lambda: current_time)
    created = service.create_job(CreateJobRequest(customer_name="Customer", description="Issue", priority="critical"))
    current_time = current_time + timedelta(hours=1, minutes=1)
    monkeypatch.setattr(main, "service", service)

    with TestClient(main.app) as client:
        response = client.get(f"/jobs/{created.id}")

    assert response.status_code == 200
    assert response.json()["sla_status"] == "breached"
    assert response.json()["sla_remaining_seconds"] == -60


def test_job_list_reports_breached_sla(monkeypatch):
    current_time = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    service = JobService(now_provider=lambda: current_time)
    service.create_job(CreateJobRequest(customer_name="Customer", description="Issue", priority="critical"))
    current_time = current_time + timedelta(hours=1, minutes=1)
    monkeypatch.setattr(main, "service", service)

    with TestClient(main.app) as client:
        response = client.get("/jobs")

    assert response.status_code == 200
    assert response.json()[0]["sla_status"] == "breached"
    assert response.json()[0]["sla_remaining_seconds"] == -60


def test_dashboard_sla_text_formatting():
    script = """
const { formatSla } = require('./app/static/app.js');
process.stdout.write(JSON.stringify([
  formatSla({ sla_status: 'within_sla', sla_remaining_seconds: 3600 }),
  formatSla({ sla_status: 'breached', sla_remaining_seconds: -300 }),
  formatSla({})
]));
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(result.stdout) == [
        "SLA: Within SLA · 1h left",
        "SLA: Breached · 5m overdue",
        "SLA: Unavailable",
    ]


@pytest.mark.parametrize("payload", [
    {}, {"customer_name": " ", "description": "Issue"},
    {"customer_name": "Customer", "description": "Issue", "priority": "urgent"},
    {"customer_name": "Customer", "description": "Issue", "status": "closed"},
])
def test_invalid_create_leaves_store_unchanged(client, payload):
    assert client.post("/jobs", json=payload).status_code == 422
    assert len(client.get("/jobs").json()) == 6
