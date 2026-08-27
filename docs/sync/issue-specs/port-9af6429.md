# Port Upstream [9af6429]: feat: derive DSH latency breakdown (TTFT, throughput, LLM vs tool time)

## Context & Upstream Delta

* **Upstream Commit:** `9af64299ffa5b96758c275324f3a059f992a36ca` (`9af6429`)
* **Author:** `Hemanth Vasi <hemanth.vasi1716@gmail.com>`
* **Date:** `2026-08-16T23:24:01+05:30`
* **Subsystems:** `backend/api, frontend/inspector, other`
* **Upstream Message:** `feat: derive DSH latency breakdown (TTFT, throughput, LLM vs tool time)`

## Specification & Porting Requirements

Derive DSH latency breakdown (TTFT, throughput, LLM vs tool time).

## Target Go Files

- `internal/scanner/parsers/dsh.go`

## Acceptance Criteria

1. **Functional Parity:** Implement equivalent logic in `repositories/tokentelemetry-go` adhering to `CONTEXT.md` domain vocabulary.
2. **Unit / Integration Tests:** Add comprehensive Go unit tests verifying edge cases and error handling (`go test -v -race ./...`).
3. **Sync Ledger Update:** Update `docs/sync/upstream-ledger.yaml` using `uv run scripts/upstream-sync.py triage 9af6429 --status ported --go-commit <sha>`.
