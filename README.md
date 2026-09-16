# Contoso Field Service

A small field-service operations dashboard for a fictitious service team. View customer incidents, assigned technicians, and priority at a glance, with search and priority filters.

Built for GitHub Copilot agentic workflow demonstrations: local feature development, pull request review, parallel issue-driven cloud work, and repository engineering instructions.

## Run locally

Requires Python 3.9 or later. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
pytest -v
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Dashboard: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

Six fictitious incidents are seeded automatically. The in-memory store resets on restart; use one server worker. This is a local demo, without authentication or durable storage.

## Architecture

| File | Responsibility |
| --- | --- |
| `app/main.py` | Thin FastAPI routes and static hosting |
| `app/models.py` | Validated Pydantic requests and domain models |
| `app/service.py` | Business logic, in-memory store, and demo data |
| `app/static/` | Plain HTML, CSS, and JavaScript dashboard |
| `tests/` | Isolated service and API tests |

The API exposes `GET /health`, `GET /jobs`, `GET /jobs/{job_id}`, and `POST /jobs`. Jobs include customer, incident description, priority, status, location, technician, and a UTC creation timestamp. Priorities are `normal`, `high`, and `critical`; baseline jobs have `open` status. New jobs can be created through Swagger and shown with the dashboard's Refresh button.

Repository-wide Copilot guidance lives in `.github/copilot-instructions.md`; path-specific guidance lives in `.github/instructions/`. `AGENTS.md` provides repository-level agent instructions. These describe architecture, validation, testing, and change discipline without relying on automatic custom-agent selection.

The service boundary and isolated tests leave room for focused additions such as SLA tracking and CSV export. Run tests before proposing changes; keep the stack simple.
