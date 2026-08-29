# Codeburn Parity Implementation Specification

**Document Status:** Approved Specification
**Target Repository:** [`repositories/tokentelemetry-go`](../../repositories/tokentelemetry-go)
**Decides:** Implementation verdicts for every gap item in [`codeburn-tokentelemetry-gap-analysis.md`](codeburn-tokentelemetry-gap-analysis.md) §2
**Supersedes:** The phased roadmap in the gap analysis (§3)
**Decision Records:** [ADR 0001 — Static Offline Pricing](../../repositories/tokentelemetry-go/docs/adr/0001-static-offline-pricing.md)
**Related:** [Research 0065](../research/0065-codeburn-tokentelemetry-gap-analysis.md) · [Web UI Parity & Search Spec](../web-ui-parity-and-search-spec.md)
**Date:** 2026-08-29

---

## 1. Decision Framework

Verdicts in this spec are **not** parity-driven. Codeburn is a reference implementation, not a target; tokentelemetry-go is a different product (single-binary collector + SQLite hub vs. zero-DB single-user CLI). Each gap was judged by a single criterion:

> **Does this improve billing correctness, or deliver insight a first-class user actually consumes, at an acceptable maintenance cost?**

Framework decisions, all confirmed by the maintainer:

1. **First-class agents:** Antigravity, GitHub Copilot, OpenCode, Cursor. These carry a standing support commitment (see `CONTEXT.md` → *First-Class Agent*). All other agents are demand-driven — added only when a user requests with evidence of real usage (the DSH precedent).
2. **Offline principle:** Model rates come exclusively from the compile-time embedded catalog plus user `pricing_overrides`. No runtime network fetch (ADR 0001).
3. **Maintenance is a cost:** Every new parser family and storage format is a standing liability. Rejection-with-trigger beats lukewarm accept-everything.
4. **Waves over phases:** Small correctness-first waves; at most one feature item per wave beyond the correctness work.

### User-group evidence (facts gathered 2026-08-29)

- Primary local agent: **Antigravity** (326 sessions, gemini-2.5-pro, $30.36 in `tokentelemetry.db`); transcripts live as `.jsonl` under `~/.gemini/antigravity/brain/`.
- Maintainer's other machines: **Copilot**, **OpenCode**. Group users: **Cursor**.
- Antigravity and Gemini CLI transcripts contain **no reasoning/thought token fields** (verified across transcript samples) — reasoning extraction has no data source for these agents today.
- Live billing bug: `gemini-3.1-pro-preview` resolves to $0.00. The embedded catalog already contains `gemini-3-1-pro-preview`; `NormalizeModelID` performs no dot→dash normalization. **Resolution robustness, not catalog staleness.**
- Antigravity `.pb` stores exist (`conversations/`, `implicit/`) but hold only 2 files locally vs. 9 `.jsonl` transcripts.

---

## 2. Verdict Summary

| # | Item | Verdict | Wave | Effort |
|---|---|---|---|---|
| **GAP-00** *(new)* | Model ID normalization bug | ✅ Accept | 1 | S |
| **GAP-01** | SQLite ingestion (Cursor, Copilot, OpenCode) | ✅ Accept | 2 | M per adapter (L total) |
| **GAP-02** | Antigravity `.pb` decoding | 🕐 Defer — probe in Wave 1 | 1 (probe) | S probe, M if built |
| **GAP-03** | `TokenUsage` extension | ✅ Accept | 1 (schema) | S–M |
| **GAP-04** | 23 missing provider adapters | ❌ Reject | — | — |
| **GAP-05** | Dynamic LiteLLM sync | ❌ Reject (auto) / 🕐 Defer (opt-in) | — | — |
| **GAP-06** | Gateway proxy peeling | 🕐 Defer | — | — |
| **GAP-07** | `BillableOutputTokens` invariant | ✅ Accept | 1 | S |
| **GAP-08** | Sub-daily time series | ✅ Accept | 3 | M |
| **GAP-09** | Quota pacing / `exhaustsAt` | ❌ Reject | — | — |
| **GAP-10** | Active decode throughput | ❌ Reject (stale claim) | — | — |
| **GAP-11** | Git session yield | 🕐 Defer | — | — |

---

## 3. Wave 1 — Billing Correctness

### 3.1 GAP-00: Model ID Normalization

**Problem.** `pricing.NormalizeModelID` only strips a static vendor-prefix list. `gemini-3.1-pro-preview` (observed, billed $0.00) never matches the catalog's `gemini-3-1-pro-preview`.

**Implementation.**
- Extend `NormalizeModelID` with version-segment dot→dash normalization after prefix stripping (`gemini-3.1-…` → `gemini-3-1-…`, `claude-3.5-…` → `claude-3-5-…`).
- Do **not** fold in gateway/suffix peeling here — that is GAP-06 and stays deferred.

**Tests.** Table-driven normalization cases built from model IDs actually observed in `tokentelemetry.db` plus catalog conventions; regression test asserting `gemini-3.1-pro-preview` resolves to the `gemini-3-1-pro-preview` rate.

**Effort.** S.

### 3.2 GAP-03: `TokenUsage` Extension

**Problem.** `models.TokenUsage` lacks `ReasoningTokens`, `CacheCreationOneHourTokens`, `CachedInputTokens`, `WebSearchRequests`; codex.go patches reasoning ad hoc; claude.go reads `Ephemeral1hInputTokens` but discards it.

**Implementation.**
- One schema migration (next file in `internal/store/migrations/`) adding the four columns to `sessions` and `message_turns` (`INTEGER NOT NULL DEFAULT 0`), plus the ingestion batch and API payload models.
- Wire extraction **only where source data exists**:
  - `codex.go`: formalize the existing `TotalTokens > gross + output` heuristic into the `ReasoningTokens` field.
  - `claude.go`: wire the already-parsed `Ephemeral1hInputTokens` into `CacheCreationOneHourTokens`.
  - Antigravity / Gemini CLI: no reasoning fields exist in transcripts (verified) — leave unwired; add a source-format TODO noting where to wire if formats grow the field.
- Pricing semantics: `CalculateCost` prices `CacheCreationOneHourTokens` at `cacheWriteRate × 1.6`; `CacheCreationTokens` (5-minute tier) at `cacheWriteRate`. The existing `×1.25` fallback applies only when the catalog lacks an explicit write rate.
- **Coordination:** the [Web UI Parity spec](../web-ui-parity-and-search-spec.md) "Enhanced Turn Ingestion Model" also touches `message_turns` (reasoning/thinking *text* blocks). Merge into the same migration window: numeric metrics here, text capture there — no duplicate migrations.
- **History:** new columns default to 0; existing rows are unchanged. Backfill is optional by clearing scanner checkpoints for codex/claude sources and re-scanning.

**Effort.** S–M.

### 3.3 GAP-07: `BillableOutputTokens` Invariant

**Problem.** No single source of truth for whether a provider bills reasoning tokens inside output (Claude, Codex, Copilot) or additively (Grok, DeepSeek, Gemini-family per Codeburn's set).

**Implementation.**
- Add `pricing.BillableOutputTokens(provider string, outputTokens, reasoningTokens int64) int64` with `REASONING_INCLUDED_IN_OUTPUT = {claude, codex, copilot}` (case-insensitive).
- Use it in `CalculateCost` and any reporting aggregation; delete codex.go's ad-hoc output adjustment in favor of it.
- Glossary terms added to `CONTEXT.md`: *Reasoning Tokens*, *Billable Output Tokens*.

**Tests.** Port the relevant reasoning-inclusion cases from Codeburn's `tests/models.test.ts`: inclusive providers (reasoning must not double-bill), additive providers (reasoning must be added), zero-reasoning turns.

**Effort.** S.

### 3.4 GAP-02 Probe: Antigravity `.pb` Coverage

**Question to answer.** Do `~/.gemini/antigravity/conversations/*.pb` and `implicit/*.pb` contain sessions/turns that the `brain/` `.jsonl` transcripts do not? (Local evidence: 2 `.pb` vs. 9 `.jsonl`.)

**Implementation.** Probe only — raw protobuf wire decode (`protoc --decode_raw` or equivalent) of the existing local files; diff session IDs and turn coverage against the parsed `.jsonl` transcripts. The `implicit/` store is the priority: it may hold sessions with no `brain/` counterpart.

**Decision gate.** Implement the `.pb` decoder (M) only if the probe finds non-overlapping data. Otherwise record as closed — `.jsonl` coverage is sufficient for the first-class Antigravity population.

**Effort.** S (probe).

---

## 4. Wave 2 — First-Class SQLite Ingestion (GAP-01)

All three remaining first-class agents keep their real data in SQLite stores that the current plaintext-only scanner cannot see. This is the highest-value work in the spec: it converts three agents from (near-)blind to first-class coverage.

### 4.1 Read-Only SQLite Reader Infrastructure

- `internal/scanner/sqlite_reader.go`: connection handling via the existing `modernc.org/sqlite` dependency, opened read-only (`_pragma=mode=ro`, `_pragma=busy_timeout=1000`), never holding write locks against a live IDE process.
- Safe BLOB→string extraction (length-guarded, invalid-UTF-8 tolerant) so corrupted stores cannot panic the collector.
- Scanner engine routing: file-type detection for `.db` / `.vscdb` / `.sqlite` sources feeding the SQLite reader instead of the text line-scanner.
- SQLite-aware checkpointing: incremental scans keyed on row identity + file mtime/hash rather than byte offsets; full re-read on store schema change.

### 4.2 Adapter Order: Cursor → Copilot → OpenCode

1. **Cursor** (first — the group users' primary agent, and today's largest blind spot: `state.vscdb` is Cursor's *primary* store; the current JSONL parser captures almost nothing):
   - `Cursor/User/globalStorage/state.vscdb` plus per-workspace storage; bubble chat reconstruction, composer data, model metadata.
2. **Copilot** (maintainer's other machines — immediate self-validation):
   - `agent-traces.db`, `session-store.db`, JetBrains storage directories; nano-AIU credit conversion (10⁹ nano-AIU = $0.01).
3. **OpenCode**:
   - `opencode*.db` session stores.

**Per-adapter requirement:** survey the store's token columns and wire any reasoning/cache fields discovered into the GAP-03 columns (the schema is already in place from Wave 1 — no second migration).

### 4.3 Acceptance Criteria

- Fixtures ported from `repositories/codeburn/tests/` for each store; parsed turn and cost outputs must match Codeburn's outputs on shared fixtures.
- No-lock verification: scanning while the IDE is open and actively writing.
- Corrupted-store resilience: malformed BLOBs and truncated files produce parse errors, never collector panics.

**Effort.** M per adapter, L total.

---

## 5. Wave 3 — Sub-Daily Time Series (GAP-08)

- Dynamic bucketing computed on demand from `message_turns` (per-turn timestamps already exist — **no schema change**): 15-minute buckets ≤ 48h, 1-hour buckets ≤ 8d, 1-day beyond.
- Hub API surface in `internal/api/stats.go` (bucketed cost/token series).
- **Coordination:** the [Web UI Parity spec](../web-ui-parity-and-search-spec.md) deliverable 5 ("time-range analytics") is the frontend consumer of this API. Design the endpoint shape jointly so it serves that spec's analytics views rather than growing a second, parallel aggregation path.
- Accepted on the basis of active dashboard investment (web UI parity work, approved 2026-08-26). Re-evaluate if dashboard adoption stalls.

**Effort.** M.

---

## 6. Deferred & Rejected Register

Every non-accepted item carries a re-entry trigger — reversing any of these is one sentence of process, not re-litigation.

| # | Item | Verdict | Re-entry trigger |
|---|---|---|---|
| GAP-02 | Antigravity `.pb` decoder | Defer (probe rides Wave 1) | Probe finds sessions/turns absent from `.jsonl` transcripts |
| GAP-04 | 23 missing provider adapters | Reject | A user requests a specific agent with evidence of real usage (DSH precedent) |
| GAP-05 | Dynamic LiteLLM sync (background) | Reject (ADR 0001) | — |
| GAP-05 | Opt-in manual refresh (`tt pricing refresh`) | Defer | A genuine staleness incident on a first-class agent that normalization cannot fix |
| GAP-06 | Gateway proxy peeling (`litellm_proxy/`, `orcarouter/`, suffixes) | Defer | First gateway-prefixed model ID observed in group telemetry |
| GAP-09 | Quota pacing / `exhaustsAt` | Reject | A group member reports a quota-window plan; note Codeburn's math is Claude-Max-shaped and would need Gemini-native semantics |
| GAP-10 | Active decode throughput | Reject (stale claim) | Explicit demand; current TTFT + DSH throughput coverage already exceeds the gap as written |
| GAP-11 | Git session yield | Defer | Explicit request from a group member |

---

## 7. Corrections to the Gap Analysis

Recorded against [`codeburn-tokentelemetry-gap-analysis.md`](codeburn-tokentelemetry-gap-analysis.md):

1. **GAP-10's premise is stale.** tokentelemetry-go already has `TTFTMsAvg` (`internal/models/session.go:72`) and DSH latency/throughput breakdowns (TTFT, throughput, LLM vs. tool time). "Only tracks turn duration" is false as of commit `c6a1df3`.
2. **The staleness narrative for GAP-05 is misdiagnosed for this user group.** The observed `gemini-3.1-pro-preview` → $0.00 failure was a resolver normalization bug (GAP-00), not an absent catalog entry — the embedded catalog already contained `gemini-3-1-pro-preview`.
3. **GAP-03 has a data-availability caveat the gap analysis misses.** Antigravity and Gemini CLI transcripts contain no reasoning/thought fields; adding schema columns alone captures nothing for those agents. Extraction is wired only where source formats provide data.
4. **Known limitation (not a gap item):** Gemini CLI transcripts on record contain no `usageMetadata` at all — gemini_cli sessions show $0.00 from data absence, not resolution failure.

---

## 8. Verification & Test Strategy

1. **Fixture parity (Wave 2):** port Codeburn's Cursor/Copilot/OpenCode test fixtures into `repositories/tokentelemetry-go/test/fixtures/`; SQLite adapters must produce identical turn and cost outputs to Codeburn on the same fixtures.
2. **Pricing parity (Wave 1):** reasoning-inclusion test cases ported from Codeburn's `models.test.ts` across inclusive and additive providers; normalization regression tests from observed model IDs.
3. **Resilience:** corrupted SQLite stores and malformed BLOBs yield parse errors, never panics; read-only scanning against live IDE processes.
4. **Performance guard:** collector parsing throughput ≥ 10,000 turns/second maintained; multi-GB rollout scans unaffected by the new code paths.

---

## 9. Issue Plan

Implementation issues live in the `tokentelemetry-go` repository:

| Issue | Scope |
|---|---|
| [#1](https://github.com/robin-paul/tokentelemetry-go/issues/1) | Wave 1 — GAP-00 model ID normalization fix (bug) |
| [#2](https://github.com/robin-paul/tokentelemetry-go/issues/2) | Wave 1 — GAP-03 TokenUsage schema + extraction |
| [#3](https://github.com/robin-paul/tokentelemetry-go/issues/3) | Wave 1 — GAP-07 BillableOutputTokens invariant |
| [#4](https://github.com/robin-paul/tokentelemetry-go/issues/4) | Wave 1 — GAP-02 Antigravity .pb probe |
| [#5](https://github.com/robin-paul/tokentelemetry-go/issues/5) | Wave 2 — SQLite reader infrastructure |
| [#6](https://github.com/robin-paul/tokentelemetry-go/issues/6) | Wave 2 — Cursor adapter (depends on #5) |
| [#7](https://github.com/robin-paul/tokentelemetry-go/issues/7) | Wave 2 — Copilot adapter (depends on #5) |
| [#8](https://github.com/robin-paul/tokentelemetry-go/issues/8) | Wave 2 — OpenCode adapter (depends on #5) |
| [#9](https://github.com/robin-paul/tokentelemetry-go/issues/9) | Wave 3 — Sub-daily bucketing API |