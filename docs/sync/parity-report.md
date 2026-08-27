# TokenTelemetry Upstream Parity & Delta Audit Report

**Generated At:** `2026-08-27T01:51:25.381649+00:00`  
**Upstream Baseline Commit:** `59f96e3` (initial-upstream-root)  
**Upstream Target HEAD:** `cecce1c`  
**Overall Parity Score:** **`96.7%`**  

---

## 1. Executive Synchronization Summary

| Metric | Count | Percentage |
| :--- | :--- | :--- |
| **Total Upstream Commits** | `426` | 100.0% |
| **Total Pull Requests** | `84` | - |
| **Ported to Go Monorepo** | `295` | 69.2% |
| **Skipped (Non-Applicable Infra)** | `121` | 28.4% |
| **In Progress** | `0` | 0.0% |
| **Deferred** | `0` | 0.0% |
| **Actionable Deltas Pending** | `10` | 2.3% |

---

## 2. Actionable Pending Deltas (Porting Backlog)

The following upstream commits represent actionable features, enhancements, or bug fixes that require porting to `repositories/tokentelemetry-go`:

| Short SHA | Subsystem | Conventional Commit Message | Target Go Files |
| :--- | :--- | :--- | :--- |
| [`67e0061`](#delta-67e0061) | `frontend/inspector` | feat(frontend): stagger mixed turns sequentially in split timeline mode | `frontend/src/components/session/TurnScrubber.tsx` |
| [`7dafe50`](#delta-7dafe50) | `frontend/inspector` | feat(frontend): support sequential timeline flow in split view | `frontend/src/components/session/TurnScrubber.tsx`<br>`frontend/src/pages/sessions/[id].astro` |
| [`2b0ed01`](#delta-2b0ed01) | `backend/api, backend/store, other` | fix(backend): fold / vs \ separator variants into one project identity | `internal/api/projects.go`<br>`internal/store/sessions.go` |
| [`8b9688d`](#delta-8b9688d) | `backend/api, frontend/inspector, other, pricing/engine` | fix(grok): read billed usage from the unified inference log | `internal/scanner/parsers/grok.go`<br>`internal/pricing/engine.go` |
| [`9af6429`](#delta-9af6429) | `backend/api, frontend/inspector, other` | feat: derive DSH latency breakdown (TTFT, throughput, LLM vs tool time) | `internal/scanner/parsers/dsh.go` |
| [`9e9f203`](#delta-9e9f203) | `backend/api, frontend/inspector, other` | feat: surface DSH sandbox mode and approval policy, incl. inherited by subagents | `internal/scanner/parsers/dsh.go` |
| [`f7a9b53`](#delta-f7a9b53) | `backend/api, docs, other` | feat: record DSH plugin lifecycle transitions via a TT-authored plugin | `internal/scanner/parsers/dsh.go` |
| [`e95f17a`](#delta-e95f17a) | `backend/api, frontend/inspector, other` | fix: report DSH's effective agent preset, not just the header's | `internal/scanner/parsers/dsh.go` |
| [`689b15d`](#delta-689b15d) | `backend/api, frontend/inspector, other` | fix: report DSH's real runtime capabilities, not another agent's config | `internal/scanner/parsers/dsh.go` |
| [`7554149`](#delta-7554149) | `backend/api, frontend/core, frontend/inspector, other` | fix: surface DeepSeek Harness across agent lists, trace, and delegation | `internal/scanner/parsers/dsh.go`<br>`frontend/src/components/session/` |

### 2.1 Detailed Actionable Delta Specifications

#### <a id="delta-67e0061"></a>1. [67e0061] feat(frontend): stagger mixed turns sequentially in split timeline mode
- **Full Commit SHA:** `67e0061460f67947aff483bf647fe4e44b4bbd7c`
- **Author:** `hwantage <hwantagexsw2@gmail.com>` | **Date:** `2026-08-25T23:21:24+09:00`
- **Subsystems:** `frontend/inspector`
- **Confidence Score:** `99%`
- **Implementation Requirements:**
  Chronological sequential staggering for mixed turns in split view mode.
- **Target Go Monorepo Files:**
  - `frontend/src/components/session/TurnScrubber.tsx`

#### <a id="delta-7dafe50"></a>2. [7dafe50] feat(frontend): support sequential timeline flow in split view
- **Full Commit SHA:** `7dafe50004d2f9f82158e6e340576aa2d8ce8ec9`
- **Author:** `hwantage <hwantagexsw2@gmail.com>` | **Date:** `2026-08-25T21:57:04+09:00`
- **Subsystems:** `frontend/inspector`
- **Confidence Score:** `99%`
- **Implementation Requirements:**
  Split view layout separating Dialogue from Brain turns in Session Inspector.
- **Target Go Monorepo Files:**
  - `frontend/src/components/session/TurnScrubber.tsx`
  - `frontend/src/pages/sessions/[id].astro`

#### <a id="delta-2b0ed01"></a>3. [2b0ed01] fix(backend): fold / vs \ separator variants into one project identity
- **Full Commit SHA:** `2b0ed01fea6fb68b2afd8fed0b717927824d099e`
- **Author:** `Rubén <ruben@grupogt.es>` | **Date:** `2026-08-22T17:28:01+02:00`
- **Subsystems:** `backend/api, backend/store, other`
- **Confidence Score:** `99%`
- **Implementation Requirements:**
  Normalize Windows vs POSIX path separators to unify project identity.
- **Target Go Monorepo Files:**
  - `internal/api/projects.go`
  - `internal/store/sessions.go`

#### <a id="delta-8b9688d"></a>4. [8b9688d] fix(grok): read billed usage from the unified inference log
- **Full Commit SHA:** `8b9688d2d3ab598169eda539350dad2c8134547d`
- **Author:** `Siren.W <sirenexcelsior@gmail.com>` | **Date:** `2026-08-21T16:32:56+08:00`
- **Subsystems:** `backend/api, frontend/inspector, other, pricing/engine`
- **Confidence Score:** `99%`
- **Implementation Requirements:**
  Extract billed token usage from ~/.grok/logs/unified.jsonl with stat caching and 128k context tiers.
- **Target Go Monorepo Files:**
  - `internal/scanner/parsers/grok.go`
  - `internal/pricing/engine.go`

#### <a id="delta-9af6429"></a>5. [9af6429] feat: derive DSH latency breakdown (TTFT, throughput, LLM vs tool time)
- **Full Commit SHA:** `9af64299ffa5b96758c275324f3a059f992a36ca`
- **Author:** `Hemanth Vasi <hemanth.vasi1716@gmail.com>` | **Date:** `2026-08-16T23:24:01+05:30`
- **Subsystems:** `backend/api, frontend/inspector, other`
- **Confidence Score:** `99%`
- **Implementation Requirements:**
  Derive DSH latency breakdown (TTFT, throughput, LLM vs tool time).
- **Target Go Monorepo Files:**
  - `internal/scanner/parsers/dsh.go`

#### <a id="delta-9e9f203"></a>6. [9e9f203] feat: surface DSH sandbox mode and approval policy, incl. inherited by subagents
- **Full Commit SHA:** `9e9f2030a436a2c5de5dc14835e209e21eecca2e`
- **Author:** `Hemanth Vasi <hemanth.vasi1716@gmail.com>` | **Date:** `2026-08-16T23:15:08+05:30`
- **Subsystems:** `backend/api, frontend/inspector, other`
- **Confidence Score:** `99%`
- **Implementation Requirements:**
  Surface DSH sandbox mode and approval policy inheritance for subagents.
- **Target Go Monorepo Files:**
  - `internal/scanner/parsers/dsh.go`

#### <a id="delta-f7a9b53"></a>7. [f7a9b53] feat: record DSH plugin lifecycle transitions via a TT-authored plugin
- **Full Commit SHA:** `f7a9b535fa2cd096642242cd24c9721254bc44ff`
- **Author:** `Hemanth Vasi <hemanth.vasi1716@gmail.com>` | **Date:** `2026-08-16T22:56:53+05:30`
- **Subsystems:** `backend/api, docs, other`
- **Confidence Score:** `99%`
- **Implementation Requirements:**
  Record DSH Cordis plugin lifecycle transitions via ~/.tokentelemetry/dsh_lifecycle.jsonl.
- **Target Go Monorepo Files:**
  - `internal/scanner/parsers/dsh.go`

#### <a id="delta-e95f17a"></a>8. [e95f17a] fix: report DSH's effective agent preset, not just the header's
- **Full Commit SHA:** `e95f17a0a3d389045882cb407d0228ca5f9dff4f`
- **Author:** `Hemanth Vasi <hemanth.vasi1716@gmail.com>` | **Date:** `2026-08-16T17:42:26+05:30`
- **Subsystems:** `backend/api, frontend/inspector, other`
- **Confidence Score:** `99%`
- **Implementation Requirements:**
  Report DSH effective agent preset in session metadata.
- **Target Go Monorepo Files:**
  - `internal/scanner/parsers/dsh.go`

#### <a id="delta-689b15d"></a>9. [689b15d] fix: report DSH's real runtime capabilities, not another agent's config
- **Full Commit SHA:** `689b15d7efe2b07f7f79d0f424fca4610f9e284f`
- **Author:** `Hemanth Vasi <hemanth.vasi1716@gmail.com>` | **Date:** `2026-08-16T17:35:33+05:30`
- **Subsystems:** `backend/api, frontend/inspector, other`
- **Confidence Score:** `99%`
- **Implementation Requirements:**
  Report DSH real runtime capabilities from session configuration.
- **Target Go Monorepo Files:**
  - `internal/scanner/parsers/dsh.go`

#### <a id="delta-7554149"></a>10. [7554149] fix: surface DeepSeek Harness across agent lists, trace, and delegation
- **Full Commit SHA:** `75541497e07b0325bc6f5d3fb53b8ed797c0bd6e`
- **Author:** `Hemanth Vasi <hemanth.vasi1716@gmail.com>` | **Date:** `2026-08-16T10:51:26+05:30`
- **Subsystems:** `backend/api, frontend/core, frontend/inspector, other`
- **Confidence Score:** `99%`
- **Implementation Requirements:**
  Surface DeepSeek Harness across agent lists, trace views, and subagent delegation trees.
- **Target Go Monorepo Files:**
  - `internal/scanner/parsers/dsh.go`
  - `frontend/src/components/session/`

---

## 3. Skipped / Non-Applicable Changes Overview

A total of **121 commits** were classified as `skipped_not_applicable`. These represent Python packaging (`requirements.lock`), Node launcher scripts (`bin/cli.js`), Next.js configuration (`next.config.ts`), or marketing website assets (`website/`) that do not apply to the pure-Go single-binary architecture.
