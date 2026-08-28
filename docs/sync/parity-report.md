# TokenTelemetry Upstream Parity & Delta Audit Report

**Generated:** `2026-08-28T20:54:50.288437+00:00`  
**Upstream Baseline:** `59f96e3`  
**Upstream HEAD:** `cecce1c`  
**Parity Percentage:** `99.3%`  

## 1. Synchronization Summary

- **Total Upstream Commits:** 426
- **Pull Requests:** 84
- **Ported to Go:** 302
- **Skipped (Non-Applicable):** 121
- **In Progress:** 0
- **Deferred:** 0
- **Actionable Deltas Pending:** 3

## 2. Actionable Pending Deltas

| Short SHA | Subsystem | Conventional Commit Message | Target Go Files |
| :--- | :--- | :--- | :--- |
| `f7a9b53` | backend/api, docs, other | feat: record DSH plugin lifecycle transitions via a TT-authored plugin | `internal/scanner/parsers/dsh.go` |
| `689b15d` | backend/api, frontend/inspector, other | fix: report DSH's real runtime capabilities, not another agent's config | `internal/scanner/parsers/dsh.go` |
| `7554149` | backend/api, frontend/core, frontend/inspector, other | fix: surface DeepSeek Harness across agent lists, trace, and delegation | `internal/scanner/parsers/dsh.go`, `frontend/src/components/session/` |