from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import ValidationError

from app.models import CreateJobRequest, Job
from app.service import JobService


@pytest.fixture
def service():
    current_time = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    return JobService(now_provider=lambda: current_time)


@pytest.fixture
def request_data():
    return CreateJobRequest(customer_name="Contoso Madrid", description="Cooling alert")


def test_create_job(service, request_data):
    job = service.create_job(request_data)
    assert isinstance(job, Job)
    assert job.id == 1
    assert job.customer_name == "Contoso Madrid"
    assert job.description == "Cooling alert"
    assert job.priority == "normal"
    assert job.status == "open"
    assert job.location == "Unspecified"
    assert job.technician == "Unassigned"
    assert job.created_at.utcoffset().total_seconds() == 0
    assert job.sla_status == "within_sla"
    assert job.sla_remaining_seconds == 24 * 60 * 60


def test_get_existing_job(service, request_data):
    job = service.create_job(request_data)
    assert service.get_job(job.id) == job


def test_get_unknown_job_returns_none(service):
    assert service.get_job(999) is None


def test_jobs_receive_sequential_ids(service, request_data):
    assert [service.create_job(request_data).id for _ in range(3)] == [1, 2, 3]


def test_list_jobs(service, request_data):
    assert service.list_jobs() == []
    jobs = [service.create_job(request_data), service.create_job(request_data)]
    assert service.list_jobs() == jobs
    service.list_jobs().clear()
    assert service.list_jobs() == jobs


@pytest.mark.parametrize("priority", ["normal", "high", "critical"])
def test_supported_priorities(service, priority):
    job = service.create_job(CreateJobRequest(
        customer_name="Customer", description="Issue", priority=priority,
        location="Madrid", technician="Elena",
    ))
    assert (job.priority, job.location, job.technician) == (priority, "Madrid", "Elena")


@pytest.mark.parametrize("field,value", [
    ("customer_name", "   "), ("description", ""), ("location", " "),
    ("technician", ""), ("priority", "urgent"), ("customer_name", "x" * 121),
    ("description", "x" * 1001), ("location", "x" * 181), ("technician", "x" * 121),
    ("status", "closed"), ("unexpected", "value"),
])
def test_invalid_input(field, value):
    data = {"customer_name": "Customer", "description": "Issue", field: value}
    with pytest.raises(ValidationError):
        CreateJobRequest(**data)


def test_input_is_trimmed():
    request = CreateJobRequest(customer_name="  Customer  ", description=" Issue ")
    assert (request.customer_name, request.description) == ("Customer", "Issue")


def test_invalid_status(request_data):
    with pytest.raises(ValidationError):
        Job(id=1, status="invalid", **request_data.model_dump())


def test_stored_job_cannot_be_mutated(service, request_data):
    job = service.create_job(request_data)
    with pytest.raises(ValidationError):
        job.customer_name = "Changed"
    assert service.get_job(job.id).customer_name == "Contoso Madrid"


def test_parallel_creates_have_unique_ids(service, request_data):
    with ThreadPoolExecutor(max_workers=4) as executor:
        jobs = list(executor.map(lambda _: service.create_job(request_data), range(20)))
    assert sorted(job.id for job in jobs) == list(range(1, 21))


def test_demo_data_is_populated_and_isolated():
    first = JobService.with_demo_data()
    second = JobService.with_demo_data()
    assert len(first.list_jobs()) == 6
    assert {job.priority for job in first.list_jobs()} == {"normal", "high", "critical"}
    first.create_job(CreateJobRequest(customer_name="New", description="Issue"))
    assert len(second.list_jobs()) == 6


@pytest.mark.parametrize("priority,expected_seconds", [
    ("critical", 60 * 60),
    ("high", 4 * 60 * 60),
    ("normal", 24 * 60 * 60),
])
def test_sla_target_by_priority(priority, expected_seconds):
    current_time = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    service = JobService(now_provider=lambda: current_time)

    job = service.create_job(CreateJobRequest(customer_name="Customer", description="Issue", priority=priority))

    assert job.sla_status == "within_sla"
    assert job.sla_remaining_seconds == expected_seconds


def test_sla_breaches_after_target_expires():
    current_time = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    service = JobService(now_provider=lambda: current_time)
    job = service.create_job(CreateJobRequest(customer_name="Customer", description="Issue", priority="critical"))

    current_time = current_time + timedelta(hours=1, minutes=5)
    breached = service.get_job(job.id)

    assert breached is not None
    assert breached.sla_status == "breached"
    assert breached.sla_remaining_seconds == -(5 * 60)
