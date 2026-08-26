# Architecture & Implementation Specification: Web Front-End Parity, Search Filters, and Deep Session Inspection

**Status:** Approved Specification  
**Canonical Map:** [Wayfinder Map #32](https://github.com/robin-paul/token-analyzer/issues/32)  
**Task Issue:** [Ticket #36](https://github.com/robin-paul/token-analyzer/issues/36)  
**Date:** 2026-08-26  

---

## 1. Executive Summary & Objective

This specification provides the architecture and phased implementation plan to bring the embedded Astro/React web interface and Go Hub backend (`tt-server`) in [`repositories/tokentelemetry-go`](file:///home/mezmo/Work/projects/acn/token-analyzer/repositories/tokentelemetry-go) to full visual and functional parity with the original Next.js implementation in [`repositories/tokentelemetry`](file:///home/mezmo/Work/projects/acn/token-analyzer/repositories/tokentelemetry).

### Core Deliverables
1. **Backend SQLite Search & Multi-Faceted Filtering**: Pure-Go SQLite FTS5 virtual tables with automatic triggers, composite indexing, and rich REST query parameter filtering in `tt-server`.
2. **Enhanced Turn Ingestion Model**: Capturing full message turn text, reasoning/thinking blocks, structured tool invocations/results, and raw payloads.
3. **Session Catalog Search & Filter UI**: Multi-criteria filtering (Agent, Model, Project, Date range, Cost, Tokens), sorting, and prompt previews in Astro/React.
4. **Deep Session Inspector**: 10 modular React packages featuring turn scrubbing, step category filtering, markdown rendering, tool call I/O & diffs, subagent trees, and artifact lightboxes.
5. **Project Workspaces & Analytics**: Grid/list view toggles, git worktree aggregation, and time-range analytics.
6. **Automated Playwright Visual Diff Harness**: Dual-server comparative testing pipeline for side-by-side visual regression verification.

---

## 2. Backend Hub (`tt-server`) Search & API Architecture

### 2.1 Pure-Go SQLite FTS5 Virtual Table & Indexing Migration
File: `internal/store/migrations/0004_search_fts_and_indexes.sql`

```sql
-- Composite B-Tree Indexes for Fast Sorting & Multi-Faceted Filtering
CREATE INDEX IF NOT EXISTS idx_sessions_cost_start ON sessions(net_cost_usd DESC, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_model_start ON sessions(model_resolved, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_agent_start ON sessions(agent_name, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_project_start ON sessions(project_name, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_total_tokens ON sessions((input_tokens + output_tokens) DESC, start_time DESC);

-- Pure-Go SQLite FTS5 External Content Table
CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
    session_id UNINDEXED,
    project_name,
    agent_name,
    model_resolved,
    git_branch,
    content='sessions',
    content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);

-- Triggers for Zero-Duplication Synchronization
CREATE TRIGGER IF NOT EXISTS sessions_ai AFTER INSERT ON sessions BEGIN
    INSERT INTO sessions_fts(rowid, session_id, project_name, agent_name, model_resolved, git_branch)
    VALUES (new.rowid, new.session_id, new.project_name, new.agent_name, new.model_resolved, new.git_branch);
END;

CREATE TRIGGER IF NOT EXISTS sessions_ad AFTER DELETE ON sessions BEGIN
    INSERT INTO sessions_fts(sessions_fts, rowid, session_id, project_name, agent_name, model_resolved, git_branch)
    VALUES ('delete', old.rowid, old.session_id, old.project_name, old.agent_name, old.model_resolved, old.git_branch);
END;

CREATE TRIGGER IF NOT EXISTS sessions_au AFTER UPDATE ON sessions BEGIN
    INSERT INTO sessions_fts(sessions_fts, rowid, session_id, project_name, agent_name, model_resolved, git_branch)
    VALUES ('delete', old.rowid, old.session_id, old.project_name, old.agent_name, old.model_resolved, old.git_branch);
    INSERT INTO sessions_fts(rowid, session_id, project_name, agent_name, model_resolved, git_branch)
    VALUES (new.rowid, new.session_id, new.project_name, new.agent_name, new.model_resolved, new.git_branch);
END;
```

### 2.2 Message Turn Domain Model Extensions
File: `internal/models/session.go`

```go
type MessageTurn struct {
    ID              int64     `json:"id" db:"id"`
    SessionID       string    `json:"session_id" db:"session_id"`
    TurnIndex       int       `json:"turn_index" db:"turn_index"`
    Role            string    `json:"role" db:"role"`
    Model           string    `json:"model" db:"model"`
    Content         string    `json:"content" db:"content"`
    Thinking        string    `json:"thinking,omitempty" db:"thinking"`
    ReasoningEffort string    `json:"reasoning_effort,omitempty" db:"reasoning_effort"`
    ToolCallsJSON   string    `json:"tool_calls,omitempty" db:"tool_calls"`
    ToolResultsJSON string    `json:"tool_results,omitempty" db:"tool_results"`
    RawPayloadJSON  string    `json:"raw_payload,omitempty" db:"raw_payload"`
    InputTokens     int64     `json:"input_tokens" db:"input_tokens"`
    OutputTokens    int64     `json:"output_tokens" db:"output_tokens"`
    CacheReadTokens int64     `json:"cache_read_tokens" db:"cache_read_tokens"`
    NetCostUSD      float64   `json:"net_cost_usd" db:"net_cost_usd"`
    DurationMS      int64     `json:"duration_ms" db:"duration_ms"`
    Timestamp       time.Time `json:"timestamp" db:"timestamp"`
}
```

### 2.3 REST API Query Parameter Surface
Endpoints: `GET /api/sessions` & `GET /api/v1/sessions`

| Query Parameter | Type | Description |
| :--- | :--- | :--- |
| `search` / `q` | string | FTS5 full-text query matching project, session ID, model, or branch (`refactor*`, `"bug fix"`). |
| `agent` | []string | Multi-select agent filter (`agent=claude_code,gemini_cli` or repeated params). |
| `model` | []string | Multi-select model filter (`model=claude-3-7-sonnet,gpt-4o`). |
| `project` | []string | Multi-select project workspace filter. |
| `since` / `start_date` | string / timestamp | ISO-8601 or Unix timestamp lower bound. |
| `until` / `end_date` | string / timestamp | ISO-8601 or Unix timestamp upper bound. |
| `min_cost` / `max_cost` | float64 | Net cost filtering bounds in USD. |
| `min_tokens` / `max_tokens`| int64 | Total token volume filtering bounds. |
| `sort_by` | enum | `start_time` (default), `cost`, `tokens`, `duration`, `relevance`. |
| `sort_order` | enum | `desc` (default), `asc`. |
| `page` / `limit` | int | Pagination parameters (default: page=1, limit=30). |
| `format` | enum | `paginated` (envelope with metadata) or `flat` (legacy array). |

---

## 3. Session Catalog UI & Search Components

File: `repositories/tokentelemetry-go/frontend/src/components/SessionList.tsx`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [🔍 Search sessions, models, projects... (300ms debounce)] [Sort: Cost ▾]    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Agents: [All] [Claude Code (12)] [Antigravity (5)] [Cursor (8)] [OpenCode] │
│ Models: [All Models ▾] | Dates: [Last 7 Days ▾] | Range: [$0.00 - $10.00+] │
├─────────────────────────────────────────────────────────────────────────────┤
│ Session / Project      │ Model            │ Tokens        │ Cost   │ Time   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🤖 claude_code         │ claude-3-7-sonnet│ 15.2k / 3.4k  │ $0.08  │ 2m ago │
│    sess_abc123 • acn   │                  │ (8k cached)   │        │        │
│    "Fix checkout flow…"│                  │               │        │        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Enhancements
1. **Debounced Search Bar** (`useDebounce(300ms)`): Syncs `q` param with browser URL history without unneeded re-renders.
2. **Multi-Faceted Filter Dropdowns**: Model selector, date range presets (Today, 7d, 30d, All), and numeric range sliders.
3. **Session Card & Table Rows**: Renders prompt context preview snippet (`"Optimize database query..."`), token badges, and direct navigation links.
4. **State Persistence**: Remembers filter states in `sessionStorage`.

---

## 4. Deep Session Inspector Architecture

File: `repositories/tokentelemetry-go/frontend/src/components/SessionDetail.tsx`  
Decomposed into 10 modular React component packages:

```
SessionDetail (Root Container)
├── SessionHeader (Agent badge, ID pill, breadcrumbs, back button)
├── SessionMetricsStrip (Cost, Total Tokens, Cache Read %, Duration, Turns)
├── TurnScrubber & PlaybackControls (600ms timer, slider, RAF smooth scroll)
├── StepIndex & StepFilterPopover (Step list, category filter badges)
├── TurnSearchInput (In-trace text search & keyword highlighting)
├── ConversationStream (Unified Single-Column vs. Split-Brain Two-Column Canvas)
│   ├── UserTurnCard (Sunken card, user prompt text)
│   ├── AssistantTurnCard (Agent accent bar, ResponseBody markdown engine)
│   ├── ReasoningCard (Amber/violet card, effort pill, encrypted box detector)
│   └── ToolInvocationCard (Collapsible JSON args, terminal output container)
├── ExecutionWaterfall (Bottom tool execution Gantt chart timeline)
├── InspectorSidebar (Right slide-out: Context, Tools, Artifacts, Raw JSON)
└── ArtifactLightboxModal (Portalled modal for images, plans, and code diffs)
```

### State Management Invariants
- `playbackIndex`: Playhead position ($0 \dots N$) controlled by scrubber slider or auto-play timer.
- `revealedCount`: High-water mark ($\max(\text{playbackIndex}, \text{revealedCount})$) preventing DOM unmounting on reverse scrubs.
- `activeStep`: Focused turn index synchronized across Step Index, Main Canvas, Waterfall, and Raw JSON view.
- `seekScrollRaf`: RAF debouncing handle ensuring high-frequency slider scrub events trigger at most 1 DOM scroll calculation per frame.

---

## 5. Project Workspaces & Analytics

### 5.1 Project Workspaces (`ProjectList.tsx` & `ProjectDetail.tsx`)
- **View Toggle**: Grid cards view vs. Dense Table view.
- **Git Worktree Aggregation**: Groups worktrees belonging to the same canonical repository under a unified parent card.
- **Project Sub-Views**: Activity feed, Plans/Artifacts viewer, and Workspace configuration.

### 5.2 Analytics Dashboard (`Analytics.tsx`)
- **Time Range Presets**: 7d, 30d, 90d, Month, Year, and Custom range.
- **Visual Charts**: Stacked AreaChart (Input vs Output vs Cache Read tokens), Agent Share PieChart, and Model Leaderboard.
- **Advanced Telemetry Breakdown**: Subagent delegation metrics, loop execution tracking, and tool invocation frequencies.

---

## 6. Automated Visual Testing & Parity Verification

File: `test/playwright/fixtures/visual/visual-diff-fixture.ts`

### Dual-Server Comparative Harness
1. **Baseline Instance**: Runs original Next.js frontend on `http://127.0.0.1:3000`.
2. **Candidate Instance**: Runs Go Astro frontend on `http://127.0.0.1:8000`.
3. **Seeded Test Database**: Both servers point to identical SQLite fixture data containing standard multi-agent sessions (Claude Code, Antigravity, Cursor, OpenCode, Copilot).
4. **Visual Capture Matrix**:
   - `01-dashboard-overview-1920x1080`
   - `02-sessions-catalog-filtered-1920x1080`
   - `03-session-inspector-turn-scrubber-1920x1080`
   - `04-session-inspector-tool-calls-1920x1080`
   - `05-projects-catalog-grid-1920x1080`
   - `06-analytics-charts-1920x1080`
   - `07-settings-pricing-overrides-1920x1080`
5. **Pixelmatch Diffing**: Automates pixel comparison with a tolerance threshold ($\le 0.5\%$ allowable layout variance for typography/anti-aliasing).

---

## 7. Implementation Roadmap & Execution Tickets

| Phase | Scope | Deliverables & Target Files |
| :--- | :--- | :--- |
| **Phase 1** | Backend SQLite FTS5 & Turn Model | `migrations/0004_search_fts_and_indexes.sql`, `internal/models/session.go`, `internal/store/` |
| **Phase 2** | Hub REST API Search & Query Builder | `internal/api/sessions.go`, `internal/store/sessions.go`, API query tests |
| **Phase 3** | Frontend Search & Filter Components | `SessionList.tsx`, `useDebounce.ts`, multi-faceted dropdowns, URL sync |
| **Phase 4** | Deep Session Inspector & Markdown | `SessionDetail.tsx`, `TurnScrubber.tsx`, `ResponseBody.tsx`, `ToolInvocationCard.tsx` |
| **Phase 5** | Projects, Worktrees & Analytics | `ProjectList.tsx`, `ProjectDetail.tsx`, `Analytics.tsx`, git worktree rollup |
| **Phase 6** | Visual Diff Playwright Suite | `test/playwright/tests/visual/`, dual-server fixture, CI visual regression check |

---
