# Port Upstream [e95f17a]: fix: report DSH's effective agent preset, not just the header's

## Context & Upstream Delta

* **Upstream Commit:** `e95f17a0a3d389045882cb407d0228ca5f9dff4f` (`e95f17a`)
* **Author:** `Hemanth Vasi <hemanth.vasi1716@gmail.com>`
* **Date:** `2026-08-16T17:42:26+05:30`
* **Subsystems:** `backend/api, frontend/inspector, other`
* **Upstream Message:** `fix: report DSH's effective agent preset, not just the header's`

## Specification & Porting Requirements

Report DSH effective agent preset in session metadata.

## Target Go Files

- `internal/scanner/parsers/dsh.go`

## Acceptance Criteria

1. **Functional Parity:** Implement equivalent logic in `repositories/tokentelemetry-go` adhering to `CONTEXT.md` domain vocabulary.
2. **Unit / Integration Tests:** Add comprehensive Go unit tests verifying edge cases and error handling (`go test -v -race ./...`).
3. **Sync Ledger Update:** Update `docs/sync/upstream-ledger.yaml` using `uv run scripts/upstream-sync.py triage e95f17a --status ported --go-commit <sha>`.
