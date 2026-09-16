# Contoso Field Service engineering standards

- Keep this application small: Python 3.9, FastAPI, Pydantic, and plain HTML/CSS/JavaScript.
- `app/main.py` contains HTTP handling and static hosting. Keep route handlers thin.
- `app/models.py` contains Pydantic/domain models and input constraints.
- `app/service.py` owns business logic and in-memory storage. Frontend code lives in `app/static/`.
- Validate all external input. Use explicit allowed values and sensible text limits.
- Do not hard-code customer-specific logic, credentials, or environment-specific URLs.
- Preserve backwards compatibility unless specifically requested otherwise.
- Add or update tests for every behavioral change. Tests must use isolated stores.
- Use Python 3.9-compatible typing, including `Optional[T]` instead of `T | None`.
- Render user-controlled text safely using DOM textContent; avoid HTML interpolation.
- Keep the dashboard accessible, responsive, and consistent with its existing visual design.
- Run `pytest -v` before completing work; verify UI interactions for frontend changes.
- Keep implementations simple. No database, frontend framework, or external service is needed for this demo.
- Do not commit or push unless explicitly requested.
