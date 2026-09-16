"""Business logic and an intentionally process-local, in-memory store."""
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Callable, Optional

from app.models import CreateJobRequest, Job, Priority


class JobService:
    SLA_TARGETS = {
        "critical": timedelta(hours=1),
        "high": timedelta(hours=4),
        "normal": timedelta(hours=24),
    }

    def __init__(self, now_provider: Optional[Callable[[], datetime]] = None):
        self._jobs: dict[int, Job] = {}
        self._next_id = 1
        self._lock = Lock()
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def _now(self) -> datetime:
        current = self._now_provider()
        if current.tzinfo is None or current.utcoffset() is None:
            raise ValueError("now_provider must return a timezone-aware datetime")
        return current.astimezone(timezone.utc)

    @classmethod
    def _sla_target(cls, priority: Priority) -> timedelta:
        return cls.SLA_TARGETS[priority]

    def _with_sla(self, job: Job, current_time: Optional[datetime] = None) -> Job:
        remaining = job.created_at + self._sla_target(job.priority) - (current_time or self._now())
        remaining_seconds = int(remaining.total_seconds())
        return Job(
            **job.model_dump(exclude={"sla_status", "sla_remaining_seconds"}),
            sla_status="within_sla" if remaining_seconds >= 0 else "breached",
            sla_remaining_seconds=remaining_seconds,
        )

    def list_jobs(self) -> list[Job]:
        with self._lock:
            jobs = list(self._jobs.values())
        return [self._with_sla(job) for job in jobs]

    def get_job(self, job_id: int) -> Optional[Job]:
        with self._lock:
            job = self._jobs.get(job_id)
        return None if job is None else self._with_sla(job)

    def create_job(self, request: CreateJobRequest) -> Job:
        current_time = self._now()
        with self._lock:
            job = Job(id=self._next_id, created_at=current_time, **request.model_dump())
            self._jobs[job.id] = job
            self._next_id += 1
        return self._with_sla(job, current_time=current_time)

    @classmethod
    def with_demo_data(cls, now_provider: Optional[Callable[[], datetime]] = None) -> "JobService":
        service = cls(now_provider=now_provider)
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
