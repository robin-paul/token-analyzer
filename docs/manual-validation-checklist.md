# TokenTelemetry Go: Local Execution & Manual Validation Guide

**Target System:** TokenTelemetry Go Rewrite (`tokentelemetry`)  
**Submodule Repository:** `repositories/tokentelemetry-go`  
**Specification Reference:** [`docs/tokentelemetry-go-architecture-spec.md`](tokentelemetry-go-architecture-spec.md)  
**Status:** Verification & QA Reference  

---

## 1. Overview

This document provides step-by-step instructions for compiling and running the single-binary **TokenTelemetry Go** implementation locally, along with a comprehensive checklist to manually validate feature parity against the legacy Python (FastAPI) and Next.js version.

---

## 2. Build and Local Execution Instructions

### Prerequisites

- **Go 1.22+**
- **Node.js 18+ & npm** (required only at build time to bundle the static Astro web assets)
- **Make**

### Step-by-Step Build & Run

1. **Navigate to the Submodule Repository:**
   ```bash
   cd repositories/tokentelemetry-go
   ```

2. **Compile Static Single Binary:**
   ```bash
   make build
   ```
   *This builds the Astro frontend static export into `internal/web/dist/`, embeds the static assets via Go `//go:embed`, and compiles a CGO-free static binary to `bin/tokentelemetry`.*

3. **Execute the Binary:**
   ```bash
   ./bin/tokentelemetry
   ```

4. **Access the Web Interface:**
   Open your browser to `http://localhost:8000/`.

---

## 3. CLI Configuration & Flags Reference

| Flag | Default | Description |
| :--- | :--- | :--- |
| `--port <int>` | `8000` | HTTP server listening port |
| `--db <path>` | `tokentelemetry.db` | SQLite database file path |
| `--scan-dir <path>` | *(empty)* | Custom directory to monitor and scan instead of default user home roots |
| `--auth-token <secret>` | `TT_AUTH_TOKEN` | Bearer token required for non-loopback network clients |
| `--no-watch` | `false` | Disable background `fsnotify` file watching and reconciler |
| `--version` | `false` | Print version and commit hash information and exit |

---

## 4. Feature Parity & Manual Validation Checklist

### A. Main Dashboard & High-Level Metrics (`/`)
- [ ] **KPI Summary Cards**: Total prompt tokens, completion tokens, gross/net cost ($ USD), total sessions, and active agent breakdown display accurately.
- [ ] **Recent Sessions Feed**: Recent agent activity appears in chronological order with agent badges (Claude Code, Gemini, Antigravity, Cursor, Codex, Copilot, Hermes, etc.).
- [ ] **Live Real-Time SSE Indicator**: Live connection heartbeat indicator stays active and updates seamlessly when new transcript logs are written to disk.

### B. Session List & Inspector (`/sessions` & `/sessions/:id`)
- [ ] **Filtering & Search**:
  - Filter sessions by Agent (`claude_code`, `antigravity`, `cursor`, `gemini_cli`, `codex`, etc.).
  - Filter by Model (`claude-3-7-sonnet`, `gemini-2.5-pro`, `gpt-4o`, etc.).
  - Search by project name, file path, or session ID.
  - Test pagination controls (`limit`, `page`).
- [ ] **Step Scrubber & Turn Breakdown**:
  - Select a session to open the Session Inspector.
  - Scrub through turns to inspect user prompts, assistant thinking/reasoning blocks, and tool invocations (`view_file`, `run_command`, etc.).
  - Verify turn-level token counts (input, output, cache read, cache creation) and individual turn cost calculations.
- [ ] **Subagent Hierarchy & Delegation**:
  - For sessions with subagents (e.g. Claude sidechains, Antigravity subagent runs, Hermes task runners), verify child session links, token attribution, and delegation tree views.

### C. Analytics & Visualizations (`/analytics`)
- [ ] **Token Volume & Cost Trends**: Interactive Recharts visualizations (daily spend, cumulative token consumption).
- [ ] **Model Leaderboard**: Model ranking table showing total prompt/completion tokens, cache hit rates, and total cost per model.
- [ ] **Timeframe Selector**: Toggle between Today, 7 Days, 30 Days, and Custom date ranges to confirm charts and metrics refresh accurately.

### D. Projects View (`/projects` & `/projects/*`)
- [ ] **Project Grouping**: Sessions are grouped accurately by repository / project directory.
- [ ] **Project Details**: Click a project to view project-specific aggregate cost, token velocity, and session history.

### E. Hermes Autonomous Agent Dashboard (`/hermes`)
- [ ] **Kanban Board**: Hermes task states (`pending`, `in_progress`, `completed`, `failed`).
- [ ] **Telemetry & Memory Overview**: Hermes telemetry metrics, skill usage stats, and agent memory views load correctly.

### F. Settings & Configuration (`/settings`)
- [ ] **Pricing Overrides**:
  - View default offline pricing table (sourced from embedded `models.dev` catalog).
  - Add a custom pricing override for a model (e.g. custom input/output cost per million tokens).
  - Verify new sessions or recosted sessions reflect the override rate.
- [ ] **Project Aliases & Hidden Projects**:
  - Set a custom display alias for a long project folder path.
  - Hide a project directory from dashboard views and confirm it disappears from the project list.
- [ ] **Hardware Power & Electricity Estimator**:
  - Configure hardware TDP wattage (e.g. Apple M-series or NVIDIA GPU) and local electricity rate ($/kWh).
  - Confirm estimated electricity cost displays alongside LLM API costs.

### G. Ingestion & File Watcher Pipeline
- [ ] **Passive Scanning**: Standard agent logs in your home directory (`~/.claude/projects/`, `~/.gemini/antigravity-cli/brain/`, `~/.cursor/`, etc.) are detected on startup.
- [ ] **Live Incremental Ingestion**: Run an agent command in a separate terminal or append lines to an existing session log. Confirm the event triggers `fsnotify`, commits to SQLite, and broadcasts a `session.created` / `session.updated` event to the web UI without needing a page refresh.
- [ ] **Checkpoint Resumption**: Restart the `./bin/tokentelemetry` process and confirm existing files are skipped via stored byte-offset checkpoints rather than duplicating records.

### H. Zero-Dependency & Storage Invariants
- [ ] **Static Compilation**: Verify binary is completely self-contained (`file bin/tokentelemetry` shows `statically linked`).
- [ ] **SQLite WAL Mode**: Verify that `tokentelemetry.db` operates in WAL mode with active `-wal` and `-shm` sidecars under write operations, supporting concurrent non-blocking reads.
