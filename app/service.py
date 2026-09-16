"""Business logic and an intentionally process-local, in-memory store."""
import csv
from io import StringIO
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

    def export_jobs_csv(self) -> str:
        with self._lock:
            output = StringIO(newline="")
            writer = csv.writer(output)
            writer.writerow(["ID", "customer", "description", "priority", "status"])
            for job in self._jobs.values():
                writer.writerow([
                    job.id,
                    job.customer_name,
                    job.description,
                    job.priority,
                    job.status,
                ])
            return output.getvalue()

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
