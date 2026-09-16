"""Thin HTTP routes and static dashboard hosting."""
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import CreateJobRequest, Job
from app.service import JobService

STATIC_DIR = Path(__file__).resolve().parent / "static"


class CSVResponse(Response):
    media_type = "text/csv"


app = FastAPI(title="Contoso Field Service API", version="1.0.0")
service = JobService.with_demo_data()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/jobs", response_model=list[Job])
def list_jobs():
    return service.list_jobs()


@app.get("/jobs/export", response_class=CSVResponse)
def export_jobs():
    return CSVResponse(
        content=service.export_jobs_csv(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="jobs.csv"'},
    )


@app.get("/jobs/{job_id}", response_model=Job)
def get_job(job_id: int):
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/jobs", response_model=Job, status_code=201)
def create_job(request: CreateJobRequest):
    return service.create_job(request)
