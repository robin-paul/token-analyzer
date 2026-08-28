# TokenTelemetry Upstream Parity & Delta Audit Report

**Generated:** `2026-08-28T20:50:14.565293+00:00`  
**Upstream Baseline:** `59f96e3`  
**Upstream HEAD:** `cecce1c`  
**Parity Percentage:** `98.8%`  

## 1. Synchronization Summary

- **Total Upstream Commits:** 426
- **Pull Requests:** 84
- **Ported to Go:** 300
- **Skipped (Non-Applicable):** 121
- **In Progress:** 0
- **Deferred:** 0
- **Actionable Deltas Pending:** 5

## 2. Actionable Pending Deltas

| Short SHA | Subsystem | Conventional Commit Message | Target Go Files |
| :--- | :--- | :--- | :--- |
| `9e9f203` | backend/api, frontend/inspector, other | feat: surface DSH sandbox mode and approval policy, incl. inherited by subagents | `internal/scanner/parsers/dsh.go` |
| `f7a9b53` | backend/api, docs, other | feat: record DSH plugin lifecycle transitions via a TT-authored plugin | `internal/scanner/parsers/dsh.go` |
| `e95f17a` | backend/api, frontend/inspector, other | fix: report DSH's effective agent preset, not just the header's | `internal/scanner/parsers/dsh.go` |
| `689b15d` | backend/api, frontend/inspector, other | fix: report DSH's real runtime capabilities, not another agent's config | `internal/scanner/parsers/dsh.go` |
| `7554149` | backend/api, frontend/core, frontend/inspector, other | fix: surface DeepSeek Harness across agent lists, trace, and delegation | `internal/scanner/parsers/dsh.go`, `frontend/src/components/session/` |