from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import ValidationError

from app.models import CreateJobRequest, Job
from app.service import JobAlreadyCompletedError, JobService


@pytest.fixture
def service():
    return JobService()


@pytest.fixture
def request_data():
    return CreateJobRequest(customer_name="Contoso Madrid", description="Cooling alert")


def test_create_job(service, request_data):
    job = service.create_job(request_data)
    assert job.id == 1
    assert job.customer_name == "Contoso Madrid"
    assert job.description == "Cooling alert"
    assert job.priority == "normal"
    assert job.status == "open"
    assert job.location == "Unspecified"
    assert job.technician == "Unassigned"
    assert job.created_at.utcoffset().total_seconds() == 0


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


def test_complete_job_sets_status_and_timestamp(service, request_data):
    job = service.create_job(request_data)
    completed = service.complete_job(job.id, "Swapped the failed unit")
    assert completed.status == "completed"
    assert completed.completion_notes == "Swapped the failed unit"
    assert completed.completed_at >= job.created_at
    assert completed.completed_at.utcoffset().total_seconds() == 0


def test_complete_job_replaces_the_stored_record(service, request_data):
    job = service.create_job(request_data)
    completed = service.complete_job(job.id)
    assert service.get_job(job.id) == completed
    assert service.get_job(job.id).status == "completed"
    assert job.status == "open"


def test_complete_job_preserves_original_fields(service, request_data):
    job = service.create_job(request_data)
    completed = service.complete_job(job.id)
    assert (completed.id, completed.customer_name, completed.description) == (job.id, job.customer_name, job.description)
    assert (completed.priority, completed.location, completed.technician) == (job.priority, job.location, job.technician)
    assert completed.created_at == job.created_at


def test_complete_job_without_notes_leaves_them_empty(service, request_data):
    completed = service.complete_job(service.create_job(request_data).id)
    assert completed.completion_notes is None


def test_complete_unknown_job_returns_none(service):
    assert service.complete_job(999) is None


def test_completing_twice_raises(service, request_data):
    job = service.create_job(request_data)
    service.complete_job(job.id)
    with pytest.raises(JobAlreadyCompletedError):
        service.complete_job(job.id)


def test_completed_job_cannot_be_mutated(service, request_data):
    completed = service.complete_job(service.create_job(request_data).id)
    with pytest.raises(ValidationError):
        completed.status = "open"


@pytest.mark.parametrize("notes", ["   ", "x" * 1001])
def test_invalid_completion_notes_are_rejected(service, request_data, notes):
    job = service.create_job(request_data)
    with pytest.raises(ValidationError):
        service.complete_job(job.id, notes)
    assert service.get_job(job.id).status == "open"


def test_completing_one_job_does_not_affect_others(service, request_data):
    first = service.create_job(request_data)
    second = service.create_job(request_data)
    service.complete_job(first.id)
    assert service.get_job(second.id).status == "open"
    assert sum(job.status == "completed" for job in service.list_jobs()) == 1
