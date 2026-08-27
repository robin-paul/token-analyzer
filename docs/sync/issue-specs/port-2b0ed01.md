# Port Upstream [2b0ed01]: fix(backend): fold / vs \ separator variants into one project identity

## Context & Upstream Delta

* **Upstream Commit:** `2b0ed01fea6fb68b2afd8fed0b717927824d099e` (`2b0ed01`)
* **Author:** `Rubén <ruben@grupogt.es>`
* **Date:** `2026-08-22T17:28:01+02:00`
* **Subsystems:** `backend/api, backend/store, other`
* **Upstream Message:** `fix(backend): fold / vs \ separator variants into one project identity`

## Specification & Porting Requirements

Normalize Windows vs POSIX path separators to unify project identity.

## Target Go Files

- `internal/api/projects.go`
- `internal/store/sessions.go`

## Acceptance Criteria

1. **Functional Parity:** Implement equivalent logic in `repositories/tokentelemetry-go` adhering to `CONTEXT.md` domain vocabulary.
2. **Unit / Integration Tests:** Add comprehensive Go unit tests verifying edge cases and error handling (`go test -v -race ./...`).
3. **Sync Ledger Update:** Update `docs/sync/upstream-ledger.yaml` using `uv run scripts/upstream-sync.py triage 2b0ed01 --status ported --go-commit <sha>`.
