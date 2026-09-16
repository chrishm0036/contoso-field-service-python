# Repository agent instructions

- Read the README and relevant source before changing behavior.
- Understand the architecture: `app/main.py` handles HTTP, `app/models.py` defines validated models, `app/service.py` owns business logic and storage, and `app/static/` contains the frontend.
- Make the smallest reasonable change. Keep Python 3.9 compatibility and use `Optional[T]`, not `T | None`.
- Preserve existing behavior and API compatibility unless the request explicitly changes it.
- Validate external input, keep route handlers thin, and keep business rules in the service layer.
- Do not add customer-specific business rules, secrets, or unnecessary dependencies.
- Add or update tests for every behavioral change. Keep test stores isolated.
- Run `pytest -v` (activate `.venv` first if needed) and verify affected frontend interactions.
- Summarize the changes, validation, and material risks or limitations.
- Do not commit or push unless explicitly asked.
