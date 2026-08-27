# Port Upstream [689b15d]: fix: report DSH's real runtime capabilities, not another agent's config

## Context & Upstream Delta

* **Upstream Commit:** `689b15d7efe2b07f7f79d0f424fca4610f9e284f` (`689b15d`)
* **Author:** `Hemanth Vasi <hemanth.vasi1716@gmail.com>`
* **Date:** `2026-08-16T17:35:33+05:30`
* **Subsystems:** `backend/api, frontend/inspector, other`
* **Upstream Message:** `fix: report DSH's real runtime capabilities, not another agent's config`

## Specification & Porting Requirements

Report DSH real runtime capabilities from session configuration.

## Target Go Files

- `internal/scanner/parsers/dsh.go`

## Acceptance Criteria

1. **Functional Parity:** Implement equivalent logic in `repositories/tokentelemetry-go` adhering to `CONTEXT.md` domain vocabulary.
2. **Unit / Integration Tests:** Add comprehensive Go unit tests verifying edge cases and error handling (`go test -v -race ./...`).
3. **Sync Ledger Update:** Update `docs/sync/upstream-ledger.yaml` using `uv run scripts/upstream-sync.py triage 689b15d --status ported --go-commit <sha>`.
