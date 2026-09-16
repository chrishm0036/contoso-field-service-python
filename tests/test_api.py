import pytest
from fastapi.testclient import TestClient

from app import main
from app.service import JobService

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "service", JobService.with_demo_data())
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
    assert client.get("/jobs/7").json() == job
    assert len(client.get("/jobs").json()) == 7


@pytest.mark.parametrize("payload", [
    {}, {"customer_name": " ", "description": "Issue"},
    {"customer_name": "Customer", "description": "Issue", "priority": "urgent"},
    {"customer_name": "Customer", "description": "Issue", "status": "closed"},
])
def test_invalid_create_leaves_store_unchanged(client, payload):
    assert client.post("/jobs", json=payload).status_code == 422
    assert len(client.get("/jobs").json()) == 6


def test_complete_job_without_notes(client):
    response = client.post("/jobs/1/complete")
    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "completed"
    assert job["completion_notes"] is None
    assert job["completed_at"] is not None
    assert client.get("/jobs/1").json() == job


def test_complete_job_with_notes(client):
    response = client.post("/jobs/2/complete", json={"completion_notes": "  Replaced the reader  "})
    assert response.status_code == 200
    assert response.json()["completion_notes"] == "Replaced the reader"


def test_completed_jobs_are_counted_in_listing(client):
    client.post("/jobs/1/complete")
    client.post("/jobs/2/complete")
    jobs = client.get("/jobs").json()
    assert len(jobs) == 6
    assert sum(job["status"] == "completed" for job in jobs) == 2
    assert sum(job["status"] == "open" for job in jobs) == 4


def test_completing_twice_returns_conflict(client):
    assert client.post("/jobs/3/complete").status_code == 200
    conflict = client.post("/jobs/3/complete")
    assert conflict.status_code == 409
    assert client.get("/jobs/3").json()["status"] == "completed"


def test_complete_unknown_job_returns_404(client):
    assert client.post("/jobs/999/complete").status_code == 404


@pytest.mark.parametrize("payload", [
    {"completion_notes": "   "},
    {"completion_notes": "x" * 1001},
    {"completion_notes": 42},
    {"unexpected": "value"},
])
def test_invalid_completion_leaves_job_open(client, payload):
    assert client.post("/jobs/4/complete", json=payload).status_code == 422
    assert client.get("/jobs/4").json()["status"] == "open"
