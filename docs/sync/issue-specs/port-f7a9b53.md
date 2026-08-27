# Port Upstream [f7a9b53]: feat: record DSH plugin lifecycle transitions via a TT-authored plugin

## Context & Upstream Delta

* **Upstream Commit:** `f7a9b535fa2cd096642242cd24c9721254bc44ff` (`f7a9b53`)
* **Author:** `Hemanth Vasi <hemanth.vasi1716@gmail.com>`
* **Date:** `2026-08-16T22:56:53+05:30`
* **Subsystems:** `backend/api, docs, other`
* **Upstream Message:** `feat: record DSH plugin lifecycle transitions via a TT-authored plugin`

## Specification & Porting Requirements

Record DSH Cordis plugin lifecycle transitions via ~/.tokentelemetry/dsh_lifecycle.jsonl.

## Target Go Files

- `internal/scanner/parsers/dsh.go`

## Acceptance Criteria

1. **Functional Parity:** Implement equivalent logic in `repositories/tokentelemetry-go` adhering to `CONTEXT.md` domain vocabulary.
2. **Unit / Integration Tests:** Add comprehensive Go unit tests verifying edge cases and error handling (`go test -v -race ./...`).
3. **Sync Ledger Update:** Update `docs/sync/upstream-ledger.yaml` using `uv run scripts/upstream-sync.py triage f7a9b53 --status ported --go-commit <sha>`.
