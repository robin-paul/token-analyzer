# Port Upstream [7dafe50]: feat(frontend): support sequential timeline flow in split view

## Context & Upstream Delta

* **Upstream Commit:** `7dafe50004d2f9f82158e6e340576aa2d8ce8ec9` (`7dafe50`)
* **Author:** `hwantage <hwantagexsw2@gmail.com>`
* **Date:** `2026-08-25T21:57:04+09:00`
* **Subsystems:** `frontend/inspector`
* **Upstream Message:** `feat(frontend): support sequential timeline flow in split view`

## Specification & Porting Requirements

Split view layout separating Dialogue from Brain turns in Session Inspector.

## Target Go Files

- `frontend/src/components/session/TurnScrubber.tsx`
- `frontend/src/pages/sessions/[id].astro`

## Acceptance Criteria

1. **Functional Parity:** Implement equivalent logic in `repositories/tokentelemetry-go` adhering to `CONTEXT.md` domain vocabulary.
2. **Unit / Integration Tests:** Add comprehensive Go unit tests verifying edge cases and error handling (`go test -v -race ./...`).
3. **Sync Ledger Update:** Update `docs/sync/upstream-ledger.yaml` using `uv run scripts/upstream-sync.py triage 7dafe50 --status ported --go-commit <sha>`.
