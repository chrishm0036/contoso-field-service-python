# Integration Assessment: PRs #10, #11, and #13

## Scope reviewed
- #10: Reject non-positive job IDs at API boundary
- #11: Refactor service wiring to FastAPI dependency injection
- #13: UX/accessibility improvements in `app/static`

## Changed files overlap

| File | #10 | #11 | #13 | Notes |
|---|---:|---:|---:|---|
| `app/main.py` | ✅ | ✅ | ❌ | **Direct overlap/conflict risk** |
| `tests/test_api.py` | ✅ | ✅ | ❌ | Same file, different areas (likely non-conflicting hunks) |
| `app/static/app.js` | ❌ | ❌ | ✅ | Isolated to frontend |
| `app/static/index.html` | ❌ | ❌ | ✅ | Isolated to frontend |
| `app/static/styles.css` | ❌ | ❌ | ✅ | Isolated to frontend |

## Conflict and duplication analysis

### 1) `app/main.py` (#10 vs #11)
These two PRs both modify the same route/import region and are **not safely auto-combinable without manual reconciliation**.

- #10 adds path validation: `job_id: int = PathParam(gt=0)`.
- #11 refactors route dependencies: `service: JobService = Depends(get_service)` and import/app-state changes.

Likely conflict points:
- `fastapi` import line (`Path as PathParam` vs `Depends` additions)
- `get_job(...)` signature (both PRs edit it)

To preserve both intents, the merged route should include **both** DI and validation (e.g., validated `job_id` plus injected `service`).

### 2) `tests/test_api.py` (#10 vs #11)
No direct logical conflict found:
- #11 updates fixture isolation approach (dependency override).
- #10 adds negative/zero ID assertions.

These are complementary and should coexist after normal merge/conflict resolution.

### 3) #13 interaction with #10/#11
No backend/API contract changes in #13. It only updates static UI behavior and styling.

Combined behavior check:
- #13 fetches `/jobs` and renders results/empty states.
- #10/#11 do not change `/jobs` response schema.
- Therefore #13 should remain compatible with both backend PRs.

## Combined-risk findings

1. **Primary integration risk:** losing one backend change during manual conflict resolution in `app/main.py`.
   - If resolved incorrectly, you may keep DI but lose `job_id > 0` validation, or vice versa.
2. **No duplicated effort requiring rollback:**
   - #10 (validation hardening), #11 (wiring refactor), #13 (UX) are distinct goals.
3. **No three-way latent break identified:**
   - No cross-cutting incompatibility found between static changes (#13) and backend refactor/validation (#10/#11).

## Recommendation

These PRs can be integrated **safely only with explicit manual conflict resolution for `app/main.py`** to retain both #10 and #11 changes. After that, #13 can be integrated independently without additional conflict risk.
