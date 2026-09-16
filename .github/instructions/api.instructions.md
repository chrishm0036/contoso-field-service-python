---
applyTo: "app/**/*.py"
---

# Python application rules

- Keep HTTP status codes, request/response handling, and routing in main.py.
- Put domain behavior and storage changes in service.py, never directly in route handlers.
- Declare and validate external data in Pydantic models in models.py.
- Reject unsupported enum values and empty or oversized text. Do not trust client-supplied state.
- Return 404 for missing jobs and use FastAPI validation responses for invalid input.
- Use timezone-aware UTC timestamps and Python 3.9-compatible typing.
- Keep job identifiers consistent and store access safe for concurrent requests.
- Preserve existing API fields and defaults unless the requested feature changes them.
- Cover business behavior with service tests and HTTP contracts with API tests.
