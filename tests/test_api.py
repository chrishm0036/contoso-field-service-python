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


def test_create_job_with_default_optional_fields(client):
    response = client.post("/jobs", json={
        "customer_name": "Test customer", "description": "New incident",
    })
    assert response.status_code == 201
    job = response.json()
    assert job["location"] == "Unspecified"
    assert job["technician"] == "Unassigned"


@pytest.mark.parametrize("payload", [
    {}, {"customer_name": " ", "description": "Issue"},
    {"customer_name": "Customer", "description": "Issue", "priority": "urgent"},
    {"customer_name": "Customer", "description": "Issue", "status": "closed"},
    {"customer_name": "\u200b", "description": "Issue"},
    {"customer_name": "Customer", "description": "Issue\u202e cod.exe"},
    {"customer_name": "Customer", "description": "Issue", "location": "Madrid\u2066Floor 2"},
    {"customer_name": "Customer", "description": "Issue", "technician": "Elena\ufeffOps"},
])
def test_invalid_create_leaves_store_unchanged(client, payload):
    assert client.post("/jobs", json=payload).status_code == 422
    assert len(client.get("/jobs").json()) == 6
