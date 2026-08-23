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

### Phase 4: Interactive TUI Dashboard (`tt watch`)

Launch `./bin/tt watch` in a dedicated terminal window:

- [ ] **Layout & Rendering**:
  - Header renders machine info, Hub status (`🟢 ONLINE`), active monitoring roots, and current timestamp.
  - KPI Cards render: `TOTAL COST (USD)`, `TOKENS (IN / OUT / CACHE)`, `CACHE HIT %`, `THROUGHPUT (t/s)`.
  - Main table displays columns: `TIME`, `AGENT`, `PROJECT`, `MODEL`, `IN / OUT / CACHE`, `COST (USD)`.
  - Footer displays stream status message and available keybindings.
- [ ] **Live Ingestion Feed**:
  - In another terminal, run `./bin/tt send --synthetic`.
  - Verify the turn table updates in real time with newly ingested message turns.
  - Verify total cost, token counters, and rolling throughput calculations update immediately.
- [ ] **Keybinding Controls**:
  - Press <kbd>p</kbd>: Stream pauses, footer shows `Stream paused (events buffered)`.
  - Press <kbd>p</kbd> again: Stream resumes.
  - Press <kbd>c</kbd>: Turn rows and token counters clear to zero.
  - Press <kbd>q</kbd> or <kbd>Ctrl+C</kbd>: Exits gracefully without terminal corruption.

---

### Phase 5: Hub REST & SSE API Verification

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

### Phase 6: Embedded Web UI Verification

Open **`http://localhost:8000/`** in a web browser:

- [ ] **Main Dashboard (`/`)**:
  - KPI summary cards display Total Net Cost, Input Tokens, Output Tokens, and Cache Efficiency.
  - Recent Sessions feed lists latest agent executions with badge icons (Claude, Gemini, Antigravity, etc.).
  - Real-time indicator confirms active SSE connection and dynamically refreshes when turns arrive.
- [ ] **Sessions Explorer (`/sessions` & `/sessions/:id`)**:
  - Filter sessions by Agent, Model, and Project name.
  - Open a session detail view: inspect turn-by-turn prompt inputs, assistant outputs, tool calls, and individual turn token costs.
  - For multi-agent sessions, verify subagent hierarchy trees and delegation trace views.
- [ ] **Projects View (`/projects` & `/projects/*`)**:
  - Verify sessions are grouped by repository/project directory.
  - Click into a specific project to verify project-level aggregated cost and token consumption.
- [ ] **Analytics View (`/analytics`)**:
  - Verify daily spend and cumulative token consumption trend charts.
  - Verify Model Leaderboard rankings (prompt/completion tokens, cache hit rate, total cost).
  - Verify date range selector updates metrics.
- [ ] **Hermes Agent Hub (`/hermes`)**:
  - Verify Hermes task Kanban board states (`pending`, `in_progress`, `completed`, `failed`).
  - Verify agent skills table, telemetry stats, and memory summaries.
- [ ] **Settings & Configuration (`/settings`)**:
  - Pricing Overrides: view catalog rates, add a custom pricing rule, and verify it persists in SQLite.
  - Hardware Power Profiler: set device TDP (W) and electricity rate ($/kWh); verify estimated electricity cost displays.
  - Budget & Retention: verify budget threshold controls and log retention settings.

---

## 5. Automated Test Suites

Run automated verification test suites across the repository:

- [ ] **Go Unit & Integration Test Suite**:
  ```bash
  cd repositories/tokentelemetry-go
  make test
  # or: go test -v -race ./...
  ```
  - Validates parsers (Antigravity, Claude, Gemini, Cursor, Codex, Copilot, Hermes, etc.), pricing engine, SQLite store/migrations, events broker, and collector pipeline.

- [ ] **End-to-End CLI-to-Hub Streaming Test**:
  ```bash
  cd repositories/tokentelemetry-go
  go test -v ./test/e2e/...
  ```
  - Spawns a transient Hub instance, tests ping health, synthetic session generation, real log ingestion, daily summary rollup, and Bearer token auth rejection.

- [ ] **Playwright End-to-End Web UI Suite**:
  ```bash
  cd repositories/tokentelemetry-go
  make test-ui
  # or smoke tests:
  make test-ui-smoke
  ```
