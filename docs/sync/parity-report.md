# TokenTelemetry Upstream Parity & Delta Audit Report

**Generated:** `2026-08-28T19:12:46.163411+00:00`  
**Upstream Baseline:** `59f96e3`  
**Upstream HEAD:** `cecce1c`  
**Parity Percentage:** `97.9%`  

## 1. Synchronization Summary

- **Total Upstream Commits:** 426
- **Pull Requests:** 84
- **Ported to Go:** 296
- **Skipped (Non-Applicable):** 121
- **In Progress:** 0
- **Deferred:** 0
- **Actionable Deltas Pending:** 9

## 2. Actionable Pending Deltas

| Short SHA | Subsystem | Conventional Commit Message | Target Go Files |
| :--- | :--- | :--- | :--- |
| `67e0061` | frontend/inspector | feat(frontend): stagger mixed turns sequentially in split timeline mode | `frontend/src/components/session/TurnScrubber.tsx` |
| `7dafe50` | frontend/inspector | feat(frontend): support sequential timeline flow in split view | `frontend/src/components/session/TurnScrubber.tsx`, `frontend/src/pages/sessions/[id].astro` |
| `2b0ed01` | backend/api, backend/store, other | fix(backend): fold / vs \ separator variants into one project identity | `internal/api/projects.go`, `internal/store/sessions.go` |
| `9af6429` | backend/api, frontend/inspector, other | feat: derive DSH latency breakdown (TTFT, throughput, LLM vs tool time) | `internal/scanner/parsers/dsh.go` |
| `9e9f203` | backend/api, frontend/inspector, other | feat: surface DSH sandbox mode and approval policy, incl. inherited by subagents | `internal/scanner/parsers/dsh.go` |
| `f7a9b53` | backend/api, docs, other | feat: record DSH plugin lifecycle transitions via a TT-authored plugin | `internal/scanner/parsers/dsh.go` |
| `e95f17a` | backend/api, frontend/inspector, other | fix: report DSH's effective agent preset, not just the header's | `internal/scanner/parsers/dsh.go` |
| `689b15d` | backend/api, frontend/inspector, other | fix: report DSH's real runtime capabilities, not another agent's config | `internal/scanner/parsers/dsh.go` |
| `7554149` | backend/api, frontend/core, frontend/inspector, other | fix: surface DeepSeek Harness across agent lists, trace, and delegation | `internal/scanner/parsers/dsh.go`, `frontend/src/components/session/` |