# TokenTelemetry Go: Local Execution & Manual Validation Guide

**Target System:** TokenTelemetry Go (`tt` Collector & `tt-server` Hub)  
**Submodule Repository:** `repositories/tokentelemetry-go`  
**Specification Reference:** [`docs/tokentelemetry-go-architecture-spec.md`](tokentelemetry-go-architecture-spec.md)  
**Domain Definitions:** [`repositories/tokentelemetry-go/CONTEXT.md`](../repositories/tokentelemetry-go/CONTEXT.md)  
**Status:** Verification & QA Reference  

---

## 1. Architecture & Overview

TokenTelemetry is organized as a high-performance distributed telemetry system:
- **Collector (`tt`)**: Local developer workstation CLI utility that passively monitors agent transcript directories, parses message turns, calculates offline financial costs, renders an interactive terminal UI (TUI), and streams ingestion batches to the Hub.
- **Hub (`tt-server`)**: Centralized telemetry backend server deployed locally or remotely, providing SQLite persistence with WAL mode, REST and SSE APIs, analytics rollups, and serving the embedded Astro Web UI.
- **Embedded Astro Frontend**: Modern reactive Web UI embedded directly inside the `tt-server` binary via Go `embed`.
- **Upstream Sync & Parity Toolset (`upstream-sync.py`)**: Local-first CLI toolset (`scripts/upstream-sync.py`) and sync ledger (`docs/sync/upstream-ledger.yaml`) that tracks upstream deltas, enforces 100% feature parity, validates schema invariants, and drafts porting specifications.

---

## 2. Build & Compilation Instructions

### Prerequisites
- **Go 1.22+**
- **Node.js 18+ & npm** (build-time only, to build Astro static frontend assets)
- **Make**

### Step-by-Step Compilation

1. **Navigate to the Submodule Repository:**
   ```bash
   cd repositories/tokentelemetry-go
   ```

2. **Build Static Web UI and Binaries:**
   ```bash
   make build-all
   ```
   *This compiles the Astro frontend (`frontend/dist` -> `internal/web/dist`), compiles the Hub server (`bin/tt-server`), and compiles the Collector CLI (`bin/tt`).*

3. **Verify Built Binaries:**
   ```bash
   ./bin/tt-server --version
   ./bin/tt --version
   ```

---

## 3. Application Startup Instructions

### A. Starting the Hub Server (`tt-server`)

The Hub hosts the SQLite database, handles ingestion batches, broadcasts real-time SSE events, and serves the Web UI.

- **Standard Local Server** (listens on port `8000` with database `tokentelemetry.db`):
  ```bash
  ./bin/tt-server --port 8000 --db tokentelemetry.db
  ```

- **Authenticated Hub Server** (requires Bearer token for remote callers):
  ```bash
  ./bin/tt-server --port 8000 --db tokentelemetry.db --auth-token "secret-telemetry-token"
  ```

- **Headless API Server** (disable local filesystem transcript watching on Hub):
  ```bash
  ./bin/tt-server --port 8000 --db tokentelemetry.db --no-watch
  ```

- **Custom Transcript Monitoring Directory**:
  ```bash
  ./bin/tt-server --port 8000 --scan-dir /path/to/transcripts
  ```

- *(Optional) Standalone Frontend Hot-Reload Development:*
  ```bash
  cd frontend
  npm run dev
  ```

---

### B. Starting the Collector CLI (`tt`)

The Collector CLI watches local transcripts and transmits telemetry to the Hub.

- **Interactive TUI Mode** (Bubble Tea live terminal dashboard):
  ```bash
  ./bin/tt watch
  # or default shorthand:
  ./bin/tt
  ```

- **Headless Background Daemon Mode** (structured `slog` output for background services/CI):
  ```bash
  ./bin/tt watch --daemon --log-level info
  ```

- **Watch Custom Root Directories**:
  ```bash
  ./bin/tt watch /path/to/transcripts /another/path/to/logs
  ```

- **Interactive Sessions Browser & Debugger (`tt sessions`)**:
  ```bash
  ./bin/tt sessions
  # or filter by agent harness:
  ./bin/tt sessions --harness antigravity --limit 10
  # or static plain-text table:
  ./bin/tt sessions --plain --limit 5
  ```

---

### C. Stopping Running Processes (`make kill`)

To terminate all running `tt-server`, `tokentelemetry`, and `tt` instances and free port `8000`:

```bash
make kill
```

---

## 4. Manual Functional Verification Checklist

### Phase 1: CLI Configuration & Environment Status (`tt config`, `tt status`)

- [ ] **Config File Path Verification**:
  ```bash
  ./bin/tt config path
  ```
  - Confirm output resolves to `~/.tokentelemetry/config.yaml`.
- [ ] **List Active Configuration**:
  ```bash
  ./bin/tt config list
  ```
  - Confirm YAML format showing `hub_url`, `auth_token`, `machine_id`, `scan_roots`, `log_level`, `batch_size`, `flush_ms`, `daemon`, `power_profile`, `max_retries`, and `timeout_sec`.
- [ ] **Get and Set Configuration Values**:
  ```bash
  ./bin/tt config set log_level debug
  ./bin/tt config get log_level
  ./bin/tt config set log_level info
  ```
  - Confirm value changes persist to `~/.tokentelemetry/config.yaml`.
- [ ] **Inspect Collector Status & Hub Health**:
  ```bash
  ./bin/tt status
  ```
  - Verify `Hub Connectivity` reports `🟢 ONLINE` with measured ping latency and server version.
  - Verify `Agent Transcript Discovery Roots` correctly lists detected local directories (e.g. `~/.claude/projects`, `~/.gemini`, `~/.cursor`, etc.) and shows active file counts.

---

### Phase 2: Transcript Scanning & Offline Costing (`tt scan`)

- [ ] **Dry-Run Scan**:
  ```bash
  ./bin/tt scan --dry-run
  ```
  - Confirm scan discovers transcript files across configured roots.
  - Verify printed metrics: `Files Discovered`, `Sessions Parsed`, `Message Turns`, `Input/Output/Cache Tokens`, `Estimated Cost ($USD)`, and `Scan Duration`.
  - Confirm mode displays `DRY RUN (No batches sent to Hub)`.
- [ ] **Grok Billed Usage & Long-Context Tier Parsing**:
  - Scan transcripts containing `~/.grok/logs/unified.jsonl` inference events (`shell.turn.inference_done`).
  - Verify parsed sessions apply accurate tiered pricing (including xAI 128k+ long-context pricing rules) rather than raw token approximations.
- [ ] **Cross-Platform Canonical Project Path Normalization**:
  - Verify scan normalizes Windows backslash (`\`) and POSIX forward slash (`/`) project root paths into a unified canonical path format at ingestion.
- [ ] **JSON Summary Output**:
  ```bash
  ./bin/tt scan --dry-run --json
  ```
  - Confirm valid, parseable JSON output matching the scan summary struct.
- [ ] **Live Transmission Scan**:
  ```bash
  ./bin/tt scan
  ```
  - Confirm batches are transmitted to Hub and report `Accepted Sessions` and `Accepted Turns`.

---

### Phase 3: Synthetic & Real Ingestion Pipeline (`tt send`)

- [ ] **Inject Synthetic Claude Session**:
  ```bash
  ./bin/tt send --synthetic --agent claude_code --project verification-demo --model claude-3-7-sonnet
  ```
  - Confirm output shows `Status: success`, a generated `Batch ID`, and `Accepted Sessions: 1`, `Accepted Turns: 2`.
- [ ] **Inject Synthetic Gemini Session**:
  ```bash
  ./bin/tt send --synthetic --agent gemini --project verification-demo --model gemini-2.5-pro
  ```
  - Confirm session ingestion completes successfully.
- [ ] **(Optional) Inject Real Transcript File**:
  ```bash
  ./bin/tt send --file /path/to/transcript.jsonl --agent claude_code --project manual-test
  ```
  - Confirm file is parsed, priced, and accepted by Hub.

---

### Phase 4: Agent Session Debugging & Inspection (`tt sessions`)

- [ ] **Static Session Listing (`--plain`)**:
  ```bash
  ./bin/tt sessions --plain --limit 5
  ```
  - Confirm output prints a structured CLI table with Session ID, Harness, Model, File Path, Duration, Turn Count, Tokens (In/Out/Cache), and Calculated Cost ($USD).
- [ ] **Filter by Harness / Agent (`--harness`)**:
  ```bash
  ./bin/tt sessions --plain --harness antigravity --limit 3
  ./bin/tt sessions --plain --harness claude_code --limit 3
  ./bin/tt sessions --plain --harness grok --limit 3
  ./bin/tt sessions --plain --harness dsh --limit 3
  ```
  - Verify only sessions matching the specified agent harness are displayed.
- [ ] **Antigravity Dynamic Model Verification**:
  ```bash
  ./bin/tt sessions --plain --harness antigravity --limit 3
  ```
  - Verify Antigravity sessions correctly report the active LLM (e.g. `gemini-3.7-flash`, `gemini-3.6-flash`, or `gemini-2.5-pro` based on `<USER_SETTINGS_CHANGE>`) instead of hardcoding to `gemini-2.5-pro`.
- [ ] **JSON Output for Scripting (`--json`)**:
  ```bash
  ./bin/tt sessions --json --limit 2 | jq .
  ```
  - Confirm valid, parseable JSON payload containing full session metadata, message turns, token usages, and subagent runs.
- [ ] **Interactive Standalone Sessions Browser**:
  ```bash
  ./bin/tt sessions --harness antigravity
  ```
  - Confirm full-screen TUI launches directly into Sessions View mode preloaded with matching sessions.

---

### Phase 5: Interactive TUI Dashboard (`tt watch`)

Launch `./bin/tt watch` in a dedicated terminal window:

- [ ] **Layout & Mode Badges**:
  - Header renders machine info, Hub status (`🟢 ONLINE`), active monitoring roots, and view mode badge (`⚡ LIVE TURNS` or `📋 SESSIONS VIEW`).
  - KPI Cards render: `THROUGHPUT (tok/s)`, `CACHE EFFICIENCY (% Hit Rate)`, `ESTIMATED COST ($USD Net/Gross)`.
  - Main view displays live turn table with columns: `TIME`, `AGENT`, `PROJECT`, `MODEL`, `IN / OUT / CACHE`, `COST (USD)`.
  - Footer displays stream status message and available interactive keybindings.
- [ ] **Live Ingestion Feed**:
  - In another terminal, run `./bin/tt send --synthetic`.
  - Verify the turn table updates in real time with newly ingested message turns.
  - Verify total cost, token counters, and rolling throughput calculations update immediately.
- [ ] **Sessions View & Split-Pane Inspector**:
  - Press <kbd>Tab</kbd> or <kbd>s</kbd>: View mode toggles between **Live Turns** and **Recent Sessions**.
  - In Sessions View:
    - Top table shows recent sessions: `TIME`, `HARNESS`, `SESSION ID`, `MODEL`, `TURNS`, `IN / OUT / CACHE`, `COST (USD)`.
    - Bottom pane renders **Session Inspector** showing file path, model resolution, tokens, duration, and turn-by-turn breakdown with tool invocations.
    - Press <kbd>↑</kbd> / <kbd>↓</kbd> or <kbd>k</kbd> / <kbd>j</kbd>: Move selection across discovered sessions; verify inspector updates to the selected session.
    - Press <kbd>Enter</kbd>: Toggle expand/collapse of the turn list in the inspector pane.
    - Press <kbd>h</kbd>: Cycle through discovered agent harnesses (e.g. `ALL AGENTS` $\rightarrow$ `ANTIGRAVITY` $\rightarrow$ `CLAUDE_CODE` $\rightarrow$ `CURSOR` $\dots$).
- [ ] **Keybinding Controls**:
  - Press <kbd>p</kbd>: Stream pauses, footer shows `Stream paused (events buffered)`.
  - Press <kbd>p</kbd> again: Stream resumes.
  - Press <kbd>c</kbd>: Turn rows, sessions, and token counters clear to zero.
  - Press <kbd>q</kbd> or <kbd>Ctrl+C</kbd>: Exits gracefully without terminal corruption.

---

### Phase 6: Hub REST & SSE API Verification

Verify Hub endpoints using `curl`:

- [ ] **System & Health Endpoints**:
  ```bash
  curl -s http://localhost:8000/healthz
  curl -s http://localhost:8000/version
  curl -s http://localhost:8000/agents
  curl -s http://localhost:8000/remote-access
  ```
- [ ] **Real-Time SSE Stream**:
  ```bash
  curl -N http://localhost:8000/events
  ```
  - In another terminal run `./bin/tt send --synthetic`. Verify `event: session_created` or `session_updated` is pushed.
- [ ] **Sessions & Analytics REST APIs**:
  ```bash
  curl -s http://localhost:8000/api/sessions | jq .
  curl -s http://localhost:8000/api/recent | jq .
  curl -s http://localhost:8000/api/stats | jq .
  curl -s http://localhost:8000/api/stats/daily | jq .
  curl -s http://localhost:8000/api/leaderboard | jq .
  curl -s http://localhost:8000/api/projects | jq .
  ```
- [ ] **SQLite FTS5 Search & Multi-Faceted Query Filtering**:
  ```bash
  # Full-text keyword search across project, model, branch, session ID
  curl -s "http://localhost:8000/api/sessions?q=fix" | jq .

  # Multi-faceted filter by agent, model, cost bounds, token bounds, and sorting
  curl -s "http://localhost:8000/api/sessions?agent=claude_code&model=claude-3-7-sonnet&min_cost=0.01&max_cost=5.00&sort_by=cost&sort_order=desc" | jq .

  # Paginated metadata format
  curl -s "http://localhost:8000/api/sessions?page=1&limit=10&format=paginated" | jq .
  ```
- [ ] **Deep Session & Turn Ingestion Inspection**:
  ```bash
  # Retrieve session details with rich message turns
  SESSION_ID=$(curl -s http://localhost:8000/api/recent | jq -r '.[0].session_id')
  curl -s "http://localhost:8000/api/sessions/${SESSION_ID}" | jq .

  # Verify deep turn fields (thinking, reasoning_effort, tool_calls, tool_results, raw_payload)
  curl -s "http://localhost:8000/api/sessions/${SESSION_ID}" | jq '.turns[0] | {role, model, thinking, reasoning_effort, tool_calls, tool_results}'
  
  # Verify DSH telemetry & posture fields (ttft_ms, generation_throughput, llm_time_ms, tool_time_ms, cache_hit_rate, sandbox_mode, approval_policy, effective_preset, preset_chain)
  curl -s "http://localhost:8000/api/sessions/${SESSION_ID}" | jq '{id, ttft_ms, generation_throughput, llm_time_ms, tool_time_ms, cache_hit_rate, sandbox_mode, approval_policy, effective_preset, preset_chain}'
  ```
- [ ] **DSH Plugin Lifecycle Ingestion Endpoints**:
  ```bash
  # Ingested transitions from ~/.tokentelemetry/dsh_lifecycle.jsonl
  curl -s http://localhost:8000/dsh/lifecycle | jq .
  curl -s http://localhost:8000/api/dsh/lifecycle | jq .
  ```
- [ ] **Pricing Catalog & Overrides API**:
  ```bash
  # Fetch embedded pricing catalog
  curl -s http://localhost:8000/api/pricing | jq .
  
  # Create a custom model pricing override
  curl -s -X POST http://localhost:8000/api/pricing/override \
    -H "Content-Type: application/json" \
    -d '{"model_pattern":"custom-model-*","input_rate":2.5,"output_rate":10.0,"cache_read_rate":0.5}'
  
  # Delete override
  curl -s -X DELETE http://localhost:8000/api/pricing/override/custom-model-*
  ```
- [ ] **Hardware Power & Meter APIs**:
  ```bash
  curl -s http://localhost:8000/config/power | jq .
  curl -s http://localhost:8000/config/power/meter | jq .
  ```
- [ ] **Hermes Autonomous Agent APIs**:
  ```bash
  curl -s http://localhost:8000/api/hermes/overview | jq .
  curl -s http://localhost:8000/api/hermes/skills | jq .
  curl -s http://localhost:8000/api/hermes/kanban | jq .
  ```

---

### Phase 7: Embedded Web UI Verification

Open **`http://localhost:8000/`** in a web browser:

- [ ] **Main Dashboard (`/`)**:
  - KPI summary cards display Total Net Cost, Input Tokens, Output Tokens, and Cache Efficiency.
  - Recent Sessions feed lists latest agent executions with badge icons (Claude, Gemini, Antigravity, etc.).
  - Real-time indicator confirms active SSE connection and dynamically refreshes when turns arrive.
- [ ] **Sessions Catalog & Search (`/sessions`)**:
  - **Debounced Search Bar**: Type in the search input (e.g. prompt keywords, branch name, session ID); verify query executes with 300ms debounce and updates the URL query string (`?q=...`).
  - **Multi-Criteria Filter Dropdowns**:
    - Filter by Agent badge pills (e.g., Claude Code, Antigravity, Cursor).
    - Filter by Model dropdown selector.
    - Filter by Date range presets (Today, Last 7 Days, Last 30 Days, All Time).
    - Filter by Cost range bounds ($Min – $Max).
    - Filter by Total Tokens volume.
  - **Sorting & Order Controls**: Toggle sort dimension (`start_time`, `cost`, `tokens`, `duration`, `relevance`) and sort direction (ASC/DESC); verify table rows sort reactively.
  - **Session Card Previews**: Verify prompt snippet preview (`"Fix checkout flow..."`), model badges, token counts, cost chips, and relative timestamps.
- [ ] **Deep Session Inspector (`/sessions/:id`)**:
  - **Split View Layout (Dialogue vs Brain)**:
    - Toggle split view button; verify Dialogue (user & assistant conversation turns) and Brain (internal thoughts, reasoning, and tool calls) render in dedicated side-by-side columns.
  - **Sequential Timeline Staggering**:
    - When Split View is enabled, toggle presentation mode between **Sequential Flow** and **Parallel Columns**.
    - In **Sequential Flow**, verify mixed turns stagger chronologically (Brain reasoning/tools appear first on the right $\rightarrow$ Assistant response follows on the left).
  - **DSH Telemetry & Posture Display**:
    - In **Context Tab**: Verify TTFT, generation throughput (excluding TTFT), LLM vs Tool time breakdown, and cache hit percentage badges.
    - In **Context & Subagents Tabs**: Verify sandbox mode, approval policy, permission presets, effective preset chain, and delegated posture inheritance (`source: "delegation"`).
  - **DSH Plugin Lifecycle Panel**:
    - In **Context Tab**: Verify plugin inventory table, Cordis FiberState statuses (`active`, `loading`, `failed`, `unloaded`), transition metrics, and time-window correlation with active session.
  - **Turn Scrubber & Playback Controls**:
    - Scrub the timeline slider ($0 \dots N$); verify playhead updates smoothly with RAF debouncing.
    - Click Play/Pause; verify the auto-stepper plays turns forward at 600ms intervals.
    - Verify high-water mark indicator (`revealedCount`) prevents turn DOM unmounting when scrubbing backwards.
  - **Category Filter Portal**:
    - Open Step Filter Popover; toggle category pills (`All`, `User`, `Assistant`, `Tools`, `Thinking`, `Errors`).
    - Verify only turns matching selected categories remain visible in the stream.
  - **In-Trace Keyword Search**:
    - Type query in `TurnSearchInput`; verify matching text is highlighted in cards and step navigation auto-focuses matching turns.
  - **Rich Message Turn Cards**:
    - `UserTurnCard`: Displays formatted user prompt text and turn timestamp.
    - `AssistantTurnCard`: Markdown response rendering (code blocks, tables, lists) and turn-level token/cost metrics.
    - `ReasoningCard`: Collapsible thought reasoning block with duration chip and effort indicator.
    - `ToolInvocationCard`: Paired tool call and tool result cards with collapsible JSON arguments, terminal stdout/stderr diff lines, error badge states, and execution duration chips.
  - **Execution Waterfall Timeline**:
    - Verify bottom Gantt chart renders tool execution spans across turn timeline.
    - Click a timeline bar; verify canvas smoothly scrolls to seek that turn.
  - **Inspector Sidebar**:
    - **Context Tab**: Displays session UUID, git branch, project workspace, tokens (in/out/cache), and net cost.
    - **Tools Histogram Tab**: Lists all invoked tools with count frequencies and cumulative duration; click tool to jump to turn.
    - **Artifacts Gallery Tab**: Displays generated file artifacts, markdown plans, and image links.
    - **Raw JSON Tab**: Syntax-highlighted raw JSON payload with one-click copy button.
  - **Portalled Artifact Lightbox Modal**:
    - Click an artifact / plan link; verify fullscreen lightbox opens with zoom controls, syntax highlighting, diff viewer, and media playback.
- [ ] **Project Workspaces (`/projects` & `/projects/*`)**:
  - **Git Worktree & Canonical Path Aggregation**: Verify worktrees belonging to the same root repository and paths with differing Windows/POSIX separators fold into the canonical parent project card with rollup metrics (∑ sessions, tokens, total cost).
  - **View Mode Toggle**: Toggle between **Grid Cards** and **Dense Table** view modes; verify preference persists across page reloads via `sessionStorage`.
  - **Multi-Column Sorting**: Sort projects by total spend, token volume, session count, or last active timestamp.
  - **Project Detail Sub-Tabs**:
    - **Activity Tab**: Recent sessions and executions within the workspace.
    - **Plans Tab**: Extracted design docs and plan artifacts.
    - **Config Tab**: Workspace settings, detection paths, and telemetry configuration.
    - Verify switching tabs synchronizes the URL (`?tab=activity|plans|config`).
- [ ] **Analytics View (`/analytics`)**:
  - **Time Range Presets**: Toggle between `7d`, `30d`, `90d`, and `All`; verify summary stats and charts update reactively.
  - **Stacked Token AreaCharts**: Verify time series charts displaying Prompt Tokens, Completion Tokens, and Cache Read Tokens.
  - **Leaderboards**: Verify Model Leaderboard and Agent Leaderboard rankings with sorting by spend, token volume, cache hit rate, and session count.
- [ ] **Hermes Agent Hub (`/hermes`)**:
  - Verify Hermes task Kanban board states (`pending`, `in_progress`, `completed`, `failed`).
  - Verify agent skills table, telemetry stats, and memory summaries.
- [ ] **Settings & Configuration (`/settings`)**:
  - **Interactive Pricing Overrides Editor**:
    - View default pricing catalog rates in table.
    - Add a custom pricing override rule (e.g. `custom-model-*`) via the UI form.
    - Verify newly created override appears in table and persists across page reloads.
    - Edit and delete custom overrides directly in the UI.
  - **Hardware Power Profiler**: Set device TDP (W) and electricity rate ($/kWh); verify estimated electricity cost displays.
  - **Budget & Retention**: Verify budget threshold alerts and log retention policy controls.

---

### Phase 8: Upstream Synchronization & Parity Toolset (`upstream-sync.py`)

Verify the zero-network local sync and parity tracking toolset:

- [ ] **Parity Status Inspection (`upstream-sync.py status`)**:
  ```bash
  uv run scripts/upstream-sync.py status
  ```
  - Confirm output reports **100.0% parity** across all 426 upstream commits and 84 PRs with `0 Actionable Deltas`.
- [ ] **Schema & Ledger Invariant Validation (`upstream-sync.py validate`)**:
  ```bash
  uv run scripts/upstream-sync.py validate
  ```
  - Verify `docs/sync/upstream-ledger.yaml` passes Pydantic schema validation, SHA uniqueness, commit topological ordering, and PR consistency rules.
- [ ] **Commit Catalog Listing & Filtering (`upstream-sync.py list`)**:
  ```bash
  uv run scripts/upstream-sync.py list --status ported --limit 5
  uv run scripts/upstream-sync.py list --status skipped --limit 5
  uv run scripts/upstream-sync.py list --focus-area dsh_telemetry
  ```
  - Verify output displays tabular list with SHA, commit summary, author date, port status, and mapped Go target files.
- [ ] **Local Offline Git Diff (`upstream-sync.py diff`)**:
  ```bash
  uv run scripts/upstream-sync.py diff cecce1c
  ```
  - Verify diff inspection displays changes against Go counterpart files without requiring network access.
- [ ] **Parity Audit Reporting & Spec Generation (`upstream-sync.py report`)**:
  ```bash
  uv run scripts/upstream-sync.py report
  ```
  - Confirm markdown parity report generation with subsystem coverage matrix and parity scores.

---

## 5. Automated Test Suites

Run automated verification test suites across the repository:

- [ ] **Upstream Sync Ledger & Invariants**:
  ```bash
  uv run scripts/upstream-sync.py validate
  ```
  - Validates ledger invariants, commit topological order, and PR consistency.

- [ ] **Workspace Alignment & Pre-Commit Hooks**:
  ```bash
  uv run pre-commit run --all-files
  ```
  - Verifies workspace alignment, docs, skills, and command configurations.

- [ ] **Go Unit & Integration Test Suite**:
  ```bash
  cd repositories/tokentelemetry-go
  make test
  # or: go test -v -race ./...
  ```
  - Validates parsers (Antigravity, Claude, Gemini, Cursor, Codex, Copilot, Hermes, Grok, DSH), pricing engine (including Grok long-context tiers), SQLite store/migrations (including FTS5, Turn schemas, and Canonical Project Paths), events broker, DSH lifecycle ingestion, and collector pipeline.

- [ ] **End-to-End CLI-to-Hub Streaming Test**:
  ```bash
  cd repositories/tokentelemetry-go
  go test -v ./test/e2e/...
  ```
  - Spawns a transient Hub instance, tests ping health, synthetic session generation, real log ingestion, daily summary rollup, and Bearer token auth rejection.

- [ ] **Playwright Regression & End-to-End Web UI Suite**:
  ```bash
  cd repositories/tokentelemetry-go
  make test-ui
  # or run specific test suites:
  cd test/playwright && npm run test:regression
  ```

- [ ] **Dual-Server Playwright Visual Regression Diff Suite**:
  ```bash
  cd repositories/tokentelemetry-go
  make test-ui-visual
  ```
  - Concurrently spins up the Next.js baseline server (`:3000`) and candidate Go Astro server (`:8000`).
  - Executes 15 standardized visual test cases (Dashboard, Sessions catalog, Session Inspector, Projects, Analytics, Settings, Nav collapsed).
  - Performs pixelmatch diffing and outputs composite side-by-side screenshots and an interactive HTML audit report to `artifacts/visual-diff/index.html`.

- [ ] **Playwright Smoke Tests**:
  ```bash
  cd repositories/tokentelemetry-go
  make test-ui-smoke
  ```
