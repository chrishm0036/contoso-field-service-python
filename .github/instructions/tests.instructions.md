---
applyTo: "tests/**/*.py"
---

# Test rules

- Use pytest and readable test names describing behavior.
- Give each test a fresh service; isolate API state with fixtures.
- Test normal behavior, invalid external input, and missing resources.
- Assert observable results, not private implementation details.
- For API changes, test HTTP status, response data, and effects on stored state.
- Avoid real network dependencies, sleeps, and fixed assumptions about the current date.
- Use Python 3.9-compatible syntax and run the full suite with `pytest -v`.
