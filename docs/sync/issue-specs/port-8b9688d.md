# Port Upstream [8b9688d]: fix(grok): read billed usage from the unified inference log

## Context & Upstream Delta

* **Upstream Commit:** `8b9688d2d3ab598169eda539350dad2c8134547d` (`8b9688d`)
* **Author:** `Siren.W <sirenexcelsior@gmail.com>`
* **Date:** `2026-08-21T16:32:56+08:00`
* **Subsystems:** `backend/api, frontend/inspector, other, pricing/engine`
* **Upstream Message:** `fix(grok): read billed usage from the unified inference log`

## Specification & Porting Requirements

Extract billed token usage from ~/.grok/logs/unified.jsonl with stat caching and 128k context tiers.

## Target Go Files

- `internal/scanner/parsers/grok.go`
- `internal/pricing/engine.go`

## Acceptance Criteria

1. **Functional Parity:** Implement equivalent logic in `repositories/tokentelemetry-go` adhering to `CONTEXT.md` domain vocabulary.
2. **Unit / Integration Tests:** Add comprehensive Go unit tests verifying edge cases and error handling (`go test -v -race ./...`).
3. **Sync Ledger Update:** Update `docs/sync/upstream-ledger.yaml` using `uv run scripts/upstream-sync.py triage 8b9688d --status ported --go-commit <sha>`.
