# Port Upstream [9e9f203]: feat: surface DSH sandbox mode and approval policy, incl. inherited by subagents

## Context & Upstream Delta

* **Upstream Commit:** `9e9f2030a436a2c5de5dc14835e209e21eecca2e` (`9e9f203`)
* **Author:** `Hemanth Vasi <hemanth.vasi1716@gmail.com>`
* **Date:** `2026-08-16T23:15:08+05:30`
* **Subsystems:** `backend/api, frontend/inspector, other`
* **Upstream Message:** `feat: surface DSH sandbox mode and approval policy, incl. inherited by subagents`

## Specification & Porting Requirements

Surface DSH sandbox mode and approval policy inheritance for subagents.

## Target Go Files

- `internal/scanner/parsers/dsh.go`

## Acceptance Criteria

1. **Functional Parity:** Implement equivalent logic in `repositories/tokentelemetry-go` adhering to `CONTEXT.md` domain vocabulary.
2. **Unit / Integration Tests:** Add comprehensive Go unit tests verifying edge cases and error handling (`go test -v -race ./...`).
3. **Sync Ledger Update:** Update `docs/sync/upstream-ledger.yaml` using `uv run scripts/upstream-sync.py triage 9e9f203 --status ported --go-commit <sha>`.
