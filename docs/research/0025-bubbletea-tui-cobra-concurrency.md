# Research Ticket #25: Bubble Tea TUI Architecture and Cobra Integration Patterns for Background Log Streaming & Status Displays

**Document ID:** `0025-bubbletea-tui-cobra-concurrency`  
**Related Ticket:** Research Ticket #25 (TokenTelemetry Go Collector `tt` & Hub Ingestion Pipeline)  
**Target Codebase:** `repositories/tokentelemetry-go/cmd/`, `repositories/tokentelemetry-go/internal/tui/`, `repositories/tokentelemetry-go/internal/collector/`  
**Status:** Complete  

---

## 1. Executive Summary & Core Architectural Invariants

The **TokenTelemetry Go Collector (`tt`)** operates as a high-performance, local workstation agent that passively monitors local filesystem directories for 18+ AI coding agent transcripts (Claude Code, Cursor, OpenCode, Codex, Gemini, Antigravity, Hermes, Copilot, etc.), incrementally parses message turns and token usage, and renders an interactive Terminal User Interface (TUI) while synchronously/asynchronously streaming ingestion batches to the centralized TokenTelemetry Hub (`tt-server`).

### Core Architectural Invariants:

1. **Decoupled Engine & UI Lifecycle**:
   - The core ingestion engine (`fsnotify` directory watcher, worker parser pool, pricing engine, batch aggregator, and HTTP upload client) operates completely independently of the presentation layer.
   - The presentation layer can be swapped dynamically between an interactive Bubble Tea TUI, a headless structured `slog` daemon, or a one-off batch sync command without altering the ingestion pipeline logic.

2. **Non-Blocking UI Invariant (Zero TUI Jitter/Freezing)**:
   - Bubble Tea’s Elm Architecture event loop (`Update` and `View`) must **never** perform disk I/O, heavy JSON parsing, database transactions, or network calls directly within the main loop.
   - External ingestion events are dispatched into Bubble Tea via thread-safe `tea.Program.Send(msg)` calls from decoupled background pipelines.

3. **Thread Safety & Race-Free Mutation**:
   - All Bubble Tea model state changes occur exclusively inside the serialized `Update(msg tea.Msg)` method.
   - Background goroutines never mutate the TUI model directly, ensuring compliance with Go's `-race` detector.

4. **Clean Terminal & Drain Invariant**:
   - On shutdown (whether initiated by TUI keybinding `q`, `Ctrl+C`, or external OS signals `SIGTERM`/`SIGINT`), the collector must:
     1. Stop accepting new filesystem events.
     2. Wait for active parsers to complete in-flight transcripts.
     3. Flush pending ingestion batches to the Hub over HTTP with a bounded timeout context.
     4. Cleanly restore the terminal state (disable raw mode, exit alternate screen, restore cursor).

---

## 2. Concurrency Architecture & Event Streaming Pipeline

### 2.1 Concurrency Topology

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 TOKEN TELEMETRY COLLECTOR (tt)                                   │
│                                                                                                  │
│  ┌───────────────────────┐                                                                       │
│  │   fsnotify Watcher    │ (Monitors ~/.claude, ~/.gemini, ~/.codex, ~/.cursor, etc.)            │
│  └───────────┬───────────┘                                                                       │
│              │ File Change Events                                                                │
│              ▼                                                                                   │
│  ┌───────────────────────┐                                                                       │
│  │ Debounce Map (250ms)  │ (Coalesces rapid file writes into discrete scan tasks)                │
│  └───────────┬───────────┘                                                                       │
│              │ Task Filepaths                                                                    │
│              ▼                                                                                   │
│  ┌───────────────────────┐                                                                       │
│  │   taskQueue (chan)    │ (Buffered task backlog, capacity 1024)                                │
│  └───────────┬───────────┘                                                                       │
│              │ Worker Dispatch                                                                   │
│              ▼                                                                                   │
│  ┌────────────────────────────────────────────────────────┐                                      │
│  │         Bounded Worker Pool (NumCPU Workers)           │                                      │
│  │  - Checkpoint Check (mtime, size, byte offset)         │                                      │
│  │  - Zero-Allocation Parser (JSONL / SQLite / Binary)    │                                      │
│  │  - Offline Pricing Engine (Cost & Power Evaluation)    │                                      │
│  └───────────────────────────┬────────────────────────────┘                                      │
│                              │ Parsed *models.Session & MessageTurn                              │
│                              ▼                                                                   │
│  ┌────────────────────────────────────────────────────────┐                                      │
│  │              Ingestion Pipeline Dispatcher             │                                      │
│  │                                                        │                                      │
│  │       ┌───────────────────────────────┐                │                                      │
│  │       │     EventSink Abstraction     │                │                                      │
│  │       └───────┬───────────────┬───────┘                │                                      │
│  └───────────────┼───────────────┼────────────────────────┘                                      │
│                  │               │                                                               │
│     [Interactive Mode]      [Headless / Daemon Mode]                                             │
│                  │               │                                                               │
│                  ▼               ▼                                                               │
│  ┌──────────────────────┐  ┌───────────────────────┐   ┌──────────────────────────────────────┐  │
│  │ tea.Program.Send(msg)│  │ slog.Logger (JSON)    │   │      HTTP Ingestion Batcher           │  │
│  │                      │  │ Output to stdout      │   │ - Accumulates turns (100ms / 50 max) │  │
│  │ Bubble Tea Elm Loop  │  └───────────────────────┘   │ - Transmits POST /api/ingest to Hub  │  │
│  │ - Top Header Status  │                              └──────────────────┬───────────────────┘  │
│  │ - Token Meters (KPI) │                                                 │                      │
│  │ - Scrollable Table   │                                                 ▼                      │
│  │ - Keybinding Footer  │                                       TokenTelemetry Hub               │
│  └──────────────────────┘                                    (Central API & Storage)             │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Event Flow & Safe External Dispatch (`tea.Program.Send`)

Bubble Tea executes the Elm Architecture via a single-threaded message processing loop in an internal goroutine. When background workers discover or parse new token turns, they must deliver those events to the TUI without taking locks inside the UI or risking race conditions.

Bubble Tea provides `tea.Program.Send(msg tea.Msg)`:
- **Thread Safety**: `Send()` is fully concurrency-safe and can be called from any number of background goroutines simultaneously.
- **Queue Semantics**: `Send()` places the message onto the program's internal event queue (`msgs chan Msg`).
- **Pre-Start Buffering**: In Bubble Tea, messages sent before `p.Run()` starts are safely buffered and delivered once the event loop initializes.
- **Error Handling**: If `Send()` is invoked after the program has terminated, it safely no-ops or returns without panicking.

---

## 3. Cobra CLI Command Tree & Lifecycle Integration

### 3.1 Command Hierarchy

The CLI binary `tt` provides standard subcommands using `github.com/spf13/cobra`:

```
tt
├── watch (default)   # Watch agent logs and stream telemetry (TUI or Headless)
├── serve / hub       # Launch the centralized Hub API server & embedded Astro dashboard
├── scan              # Run a one-off disk scan and print summary / sync to Hub
├── status            # Query Hub health, current token totals, and active watchers
└── config            # Manage model pricing overrides, hardware profiles, and Hub URL
```

---

## 4. Responsive Terminal UI Styling with Lip Gloss

Lip Gloss (`github.com/charmbracelet/lipgloss`) is used to construct a responsive, full-screen grid layout that dynamically recalculates on every `tea.WindowSizeMsg`.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│  TOKEN TELEMETRY v1.0.0      ● HUB: ONLINE (http://localhost:8000)       WATCHING: 7 AGENTS   │  <- Header (Fixed 3 rows)
├────────────────────────────────┬───────────────────────────────┬───────────────────────────────┤
│ THROUGHPUT                     │ CACHE EFFICIENCY              │ ESTIMATED COST                │  <- KPI Meters (Fixed 5 rows)
│ 1,420 tok/s  (▲ 240)           │ 68.4% Hit Rate                │ $14.82 Net ($22.40 Gross)     │
│ 12 turns/min                   │ 1.2M Saved Tokens             │ $0.14 Electricity (1.1 kWh)   │
├────────────────────────────────┴───────────────────────────────┴───────────────────────────────┤
│ TIME      AGENT       PROJECT             MODEL                 TOKENS (IN/OUT/CACHE)     COST │  <- Live Feed Table (bubbles/table)
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 14:02:11  Claude      tokentelemetry      claude-3-7-sonnet     1,240 / 412 / 8,192     $0.024 │
│ 14:02:18  Codex       fintech-platform    o3-mini               4,510 / 890 / 0         $0.018 │
│ 14:02:25  Cursor      react-dashboard     claude-3-5-sonnet     890 / 240 / 16,384      $0.008 │
│ 14:02:30  Hermes      db-optimizer        deepseek-r1           12,400 / 1,200 / 0      $0.032 │
│ 14:02:44  Antigrav    infra-terraform     gemini-2.5-pro        2,100 / 650 / 4,096     $0.011 │
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [q] quit  [c] clear  [p] pause/resume  [t] filter agent  [↑/↓] scroll  [enter] inspect turn   │  <- Status Footer (Fixed 1-2 rows)
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Headless vs. Interactive Mode Switching

- In **Interactive TUI Mode**: All `slog` output is redirected to a rotating file (`~/.tokentelemetry/logs/collector.log`).
- In **Headless Mode**: `slog` writes directly to `os.Stdout` (formatted as JSON or ANSI text depending on `--log-format`).
