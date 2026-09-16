"""Business logic and an intentionally process-local, in-memory store."""
from threading import Lock
from typing import Optional

from app.models import CreateJobRequest, Job


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

    def update_priority(self, job_id: int, priority: str) -> Optional[Job]:
        """Change the priority of an existing job.

        Jobs are frozen, so the stored record is replaced with an updated copy.
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            data = job.model_dump()
            data["priority"] = priority
            updated = Job(**data)
            self._jobs[job_id] = updated
            return updated

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
