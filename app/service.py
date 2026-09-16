"""Business logic and an intentionally process-local, in-memory store."""
from datetime import datetime, timezone
from threading import Lock
from typing import Optional

from app.models import CreateJobRequest, Job


class JobAlreadyCompletedError(Exception):
    """Raised when an operator tries to complete a job that is already resolved."""


class JobService:
    def __init__(self):
        self._jobs: dict[int, Job] = {}
        self._next_id = 1
        self._lock = Lock()

    def list_jobs(self) -> list[Job]:
        with self._lock:
            return list(self._jobs.values())

    def get_job(self, job_id: int) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def create_job(self, request: CreateJobRequest) -> Job:
        with self._lock:
            job = Job(id=self._next_id, **request.model_dump())
            self._jobs[job.id] = job
            self._next_id += 1
            return job

    def complete_job(self, job_id: int, completion_notes: Optional[str] = None) -> Optional[Job]:
        """Resolve an open job. Returns None when the job does not exist.

        Jobs are frozen, so completion replaces the stored record with a
        revalidated copy rather than mutating it in place.
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            if job.status == "completed":
                raise JobAlreadyCompletedError(f"Job {job_id} is already completed")
            data = job.model_dump()
            data.update(
                status="completed",
                completed_at=datetime.now(timezone.utc),
                completion_notes=completion_notes,
            )
            completed = Job(**data)
            self._jobs[job_id] = completed
            return completed

    @classmethod
    def with_demo_data(cls) -> "JobService":
        service = cls()
        examples = [
            ("Contoso Madrid", "Server room cooling alert", "critical", "Madrid · Castellana campus", "Elena García"),
            ("Fabrikam Barcelona", "Access-control reader failure", "high", "Barcelona · Innovation hub", "Marc Soler"),
            ("Northwind Valencia", "Network cabinet temperature warning", "normal", "Valencia · Logistics centre", "Lucía Torres"),
            ("Adventure Works Bilbao", "Connectivity outage", "critical", "Bilbao · Regional office", "Diego Martín"),
            ("Contoso Madrid", "Meeting room display intermittently offline", "normal", "Madrid · Castellana campus", "Elena García"),
            ("Fabrikam Barcelona", "Backup power unit requires inspection", "high", "Barcelona · Innovation hub", "Marc Soler"),
        ]
        for customer, description, priority, location, technician in examples:
            service.create_job(CreateJobRequest(
                customer_name=customer, description=description, priority=priority,
                location=location, technician=technician,
            ))
        return service
