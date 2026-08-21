# TokenTelemetry Go Single-Binary Architecture & Implementation Specification

**Document Version:** 1.0.0  
**Target System:** TokenTelemetry Go Rewrite (`tokentelemetry`)  
**Status:** Canonical Implementation Guide  
**Source Specification Issues:** [#1](https://github.com/robin-paul/token-analyzer/issues/1), [#2](https://github.com/robin-paul/token-analyzer/issues/2), [#3](https://github.com/robin-paul/token-analyzer/issues/3), [#4](https://github.com/robin-paul/token-analyzer/issues/4), [#5](https://github.com/robin-paul/token-analyzer/issues/5), [#6](https://github.com/robin-paul/token-analyzer/issues/6), [#7](https://github.com/robin-paul/token-analyzer/issues/7), [#8](https://github.com/robin-paul/token-analyzer/issues/8)  

---

## 1. Executive Summary & Core Architectural Invariants

### 1.1 Purpose
This document specifies the complete target architecture, data structures, concurrency models, file formats, REST/SSE interfaces, and migration strategies to port **TokenTelemetry** from its legacy dual-tier Python (FastAPI) and Next.js codebase into a **high-performance, zero-dependency, single deployable Go executable**.

### 1.2 Core Architectural Invariants
1. **Single Static Binary**: The entire system—backend REST API, real-time SSE streamer, transcript file watcher, 18+ agent parsers, offline pricing engine, SQLite database engine, and the static Astro Web UI—must compile into a single static binary without external runtime dependencies (no Node.js, Python, or dynamic C libraries required at runtime).
2. **CGO-Free Pure-Go SQLite**: Use `modernc.org/sqlite` to enable static cross-compilation across all major operating systems (`linux/amd64`, `linux/arm64`, `darwin/amd64`, `darwin/arm64`, `windows/amd64`) without requiring a C compiler toolchain.
3. **Embedded Static Astro Frontend with React Client Islands**: Pre-render all standard dashboard views to static HTML/CSS/JS via Astro, embedding the compiled output into the Go binary using Go's `//go:embed`. Dynamic and high-interactivity components (Analytics charts, Session Inspector step-scrubber, Hermes Kanban board) are hydrated on the client via React 19 islands.
4. **Passive On-Disk Ingestion & Checkpointing**: Parse agent log directories passively from disk (no active HTTP proxying) using a debounced `fsnotify` event stream combined with a 60-second background reconciler ticker. Track incremental byte offsets and file modification timestamps to prevent redundant re-parsing.
5. **Two-Tier Offline Pricing & Power Estimation**: Estimate monetary LLM costs and local hardware electricity usage completely offline using an embedded pricing dataset (`pricing_data.json`) supplemented with database user overrides.

---

## 2. High-Level Architecture & Concurrency Topology

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                TOKEN TELEMETRY (GO BINARY)                             │
│                                                                                        │
│  ┌─────────────────────────┐   HTTP / SSE (Single Port :8000)   ┌───────────────────┐  │
│  │   Embedded Astro Web    │ ◄────────────────────────────────► │     chi Router    │  │
│  │ (React Client Islands)  │                                    │  & Auth / CORS MW │  │
│  └─────────────────────────┘                                    └─────────┬─────────┘  │
│                                                                           │            │
│  ┌────────────────────────────────────────────────────────┐               │            │
│  │                    Events Broker                       │ ◄─────────────┤            │
│  │      (Real-time SSE Broadcast & Heartbeat Hub)         │               │            │
│  └──────────────────────────▲─────────────────────────────┘               │            │
│                             │                                             ▼            │
│  ┌──────────────────────────┴─────────────────────────────┐     ┌───────────────────┐  │
│  │             Scanner & Watcher Concurrency              │     │   REST Handlers   │  │
│  │  ┌──────────────┐     ┌──────────────┐     ┌─────────┐ │     │ (40+ Endpoints)   │  │
│  │  │ fsnotify     │ ──► │ Bounded      │ ──► │ Batch   │ │     └─────────┬─────────┘  │
│  │  │ Watcher      │     │ Worker Pool  │     │ Channel │ │               │            │
│  │  │ + Reconciler │     │ (18+ Parsers)│     │ Commit  │ │               │            │
│  │  └──────────────┘     └──────────────┘     └────┬────┘ │               │            │
│  └─────────────────────────────────────────────────┼──────┘               │            │
│                                                    │                      │            │
│                                                    ▼                      ▼            │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                         Pure-Go SQLite Engine (WAL Mode)                         │  │
│  │  ┌──────────────────────────────────────┐  ┌──────────────────────────────────┐  │  │
│  │  │  Dedicated Single-Writer Connection  │  │  Multi-Connection Read Pool      │  │  │
│  │  │  (SetMaxOpenConns(1) / Serialized)   │  │  (SetMaxOpenConns(2 * NumCPU))   │  │  │
│  │  └──────────────────────────────────────┘  └──────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Go Package & Directory Layout

The repository is organized following standard Go project layout principles with deep package encapsulation in `internal/`:

```
tokentelemetry/
├── cmd/
│   └── tokentelemetry/
│       └── main.go                 # Entrypoint: CLI flag parsing, signal handling, server lifecycle
├── internal/
│   ├── api/                        # HTTP routing, REST handlers, middleware, request/response DTOs
│   │   ├── router.go               # chi router registration & SPA fallback
│   │   ├── middleware.go           # Bearer auth, CORS, logging, gzip recovery
│   │   ├── sessions.go             # /api/sessions, /api/recent, /api/agent-sessions
│   │   ├── analytics.go            # /api/stats, /api/leaderboard, /api/charts
│   │   ├── hermes.go               # /api/hermes/* handlers
│   │   ├── config.go               # /api/config, /api/settings, /api/pricing
│   │   └── health.go               # /healthz, /version
│   ├── events/                     # Real-time event streaming & SSE
│   │   ├── broker.go               # Central thread-safe SSE subscriber hub
│   │   └── messages.go             # SSE event payloads (session.new, session.update, scan.progress)
│   ├── scanner/                    # Agent transcript scanning & parsing engine
│   │   ├── engine.go               # Orchestrator, worker pool, discovery manager
│   │   ├── checkpoint.go           # File state tracking (mtime, size, byte offset)
│   │   ├── parsers/                # Agent-specific parser implementations
│   │   │   ├── parser.go           # Parser interface & TranscriptChunk struct
│   │   │   ├── claude.go           # Claude Code parser (~/.claude/projects)
│   │   │   ├── codex.go            # OpenAI Codex CLI parser (~/.codex/sessions)
│   │   │   ├── gemini.go           # Gemini CLI parser (~/.gemini)
│   │   │   ├── antigravity.go      # Antigravity CLI parser (~/.gemini/antigravity-cli)
│   │   │   ├── qwen.go             # Qwen Code parser (~/.qwen)
│   │   │   ├── cursor.go           # Cursor IDE transcripts & state.vscdb
│   │   │   ├── copilot.go          # GitHub Copilot CLI & VS Code logs
│   │   │   ├── opencode.go         # OpenCode parser
│   │   │   ├── hermes.go           # Hermes autonomous agent telemetry
│   │   │   ├── grok.go             # Grok Build parser
│   │   │   ├── pi.go               # Pi Coding Agent parser
│   │   │   ├── cline.go            # Cline extension parser
│   │   │   ├── metamuse.go         # Meta Muse parser
│   │   │   ├── prime.go            # Prime Agent parser
│   │   │   ├── smallcode.go        # SmallCode parser
│   │   │   ├── dsh.go              # DeepSeek Harness (dsh) parser
│   │   │   ├── roo.go              # Roo Code parser
│   │   │   └── windsurf.go         # Windsurf / Cascade parser
│   ├── watcher/                    # Log filesystem watcher
│   │   ├── watcher.go              # fsnotify directory watcher & debouncing
│   │   └── reconciler.go           # 60s fallback ticker reconciler
│   ├── pricing/                    # Two-tier pricing engine & cost calculator
│   │   ├── engine.go               # Pricing calculation, cache multipliers, TTL partitions
│   │   ├── dataset.go              # Embedded models.dev pricing table loader
│   │   ├── resolver.go             # Fuzzy longest-prefix model name matching
│   │   └── power.go                # Hardware profile power/electricity estimation
│   ├── store/                      # Pure-Go SQLite persistence layer
│   │   ├── db.go                   # Connection initialization & WAL pragma configuration
│   │   ├── migrations/             # Embedded SQL migration scripts
│   │   │   ├── 0001_initial.sql
│   │   │   └── 0002_indexes.sql
│   │   ├── migrator.go             # Schema migration runner
│   │   ├── sessions.go             # Session & message turn queries
│   │   ├── summaries.go            # Daily summary rollups & aggregations
│   │   └── checkpoints.go          # Scanner checkpoint persistence
│   ├── models/                     # Shared domain entities
│   │   ├── session.go              # Session, MessageTurn, SubagentRun
│   │   ├── pricing.go              # ModelRate, PricingOverride, PowerConfig
│   │   └── summary.go              # DailySummary, LeaderboardEntry, FilterParams
│   └── web/                        # Embedded Astro static assets
│       ├── assets.go               # //go:embed all:dist and http.FS handler
│       └── dist/                   # Static build output from frontend/
├── frontend/                       # Astro static web application
│   ├── package.json
│   ├── astro.config.mjs
│   ├── tailwind.config.mjs
│   ├── src/
│   │   ├── layouts/                # BaseLayout.astro, DashboardLayout.astro
│   │   ├── pages/                  # Static routes (index.astro, analytics.astro, etc.)
│   │   ├── components/             # React Client Islands (Inspector, Charts, Kanban)
│   │   ├── lib/                    # API client, formatting helpers, brand tokens
│   │   └── styles/                 # Tailwind CSS v4 globals.css
├── Makefile                        # Unified build, test, and release targets
└── go.mod
```

---

## 4. Pure-Go SQLite Database & Schema Specification

### 4.1 Driver & Pragmas
Database operations use `modernc.org/sqlite`. The connection pool is split into a **single-writer connection** and a **multi-reader pool** to prevent `SQLITE_BUSY` contention while permitting parallel HTTP reads.

```go
// Connection Pool Initialization
db, err := sql.Open("sqlite", "file:tokentelemetry.db?_pragma=busy_timeout(5000)")
if err != nil {
    return nil, err
}

// Global Pragmas executed on startup
pragmas := []string{
    "PRAGMA journal_mode = WAL;",
    "PRAGMA busy_timeout = 5000;",
    "PRAGMA synchronous = NORMAL;",
    "PRAGMA foreign_keys = ON;",
    "PRAGMA cache_size = -64000;", // 64MB memory cache
    "PRAGMA temp_store = MEMORY;",
}
for _, p := range pragmas {
    if _, err := db.Exec(p); err != nil {
        return nil, fmt.Errorf("pragma %s failed: %w", p, err)
    }
}

// Pool Constraints
db.SetMaxOpenConns(max(4, runtime.NumCPU() * 2))
db.SetMaxIdleConns(max(2, runtime.NumCPU()))
db.SetConnMaxLifetime(0)
```

### 4.2 Relational DDL Schema (`0001_initial.sql`)

```sql
-- 1. Schema Migrations Tracker
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Sessions (Primary conversation / execution units)
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,                       -- UUID or deterministic hash (agent:filepath:id)
    session_id TEXT NOT NULL,                  -- Native session ID from agent transcript
    agent_name TEXT NOT NULL,                  -- 'claude_code', 'gemini_cli', 'codex', etc.
    project_name TEXT NOT NULL,                -- Resolved project name / folder basename
    file_path TEXT NOT NULL UNIQUE,            -- Absolute path to transcript file
    created_at TIMESTAMP NOT NULL,             -- Session start timestamp
    updated_at TIMESTAMP NOT NULL,             -- Last updated timestamp
    start_time TIMESTAMP NOT NULL,             -- First message timestamp
    end_time TIMESTAMP NOT NULL,               -- Last message timestamp
    duration_seconds REAL DEFAULT 0,           -- Total active wall-clock time
    model_raw TEXT NOT NULL,                   -- Raw model name from log (e.g. 'claude-3-7-sonnet-20250219')
    model_resolved TEXT NOT NULL,              -- Canonical model name for pricing lookup
    input_tokens INTEGER DEFAULT 0,            -- Total net prompt tokens
    output_tokens INTEGER DEFAULT 0,           -- Total completion tokens
    cache_read_tokens INTEGER DEFAULT 0,       -- Prompt cache hit tokens
    cache_creation_tokens INTEGER DEFAULT 0,   -- Prompt cache write tokens
    gross_cost_usd REAL DEFAULT 0,             -- Cost without cache discounts
    net_cost_usd REAL DEFAULT 0,               -- True billable cost with cache discounts
    electricity_cost_usd REAL DEFAULT 0,       -- Estimated hardware power cost
    hardware_profile TEXT DEFAULT 'default',   -- CPU/GPU profile identifier
    status TEXT DEFAULT 'completed',           -- 'active', 'completed', 'error'
    git_branch TEXT DEFAULT '',                -- Associated git branch name
    is_subagent BOOLEAN DEFAULT 0,             -- 1 if spawned by parent orchestrator
    parent_session_id TEXT DEFAULT '',         -- ID of parent orchestrator session
    subagent_type TEXT DEFAULT ''              -- Subagent role/type ('research', 'planner', etc.)
);

-- 3. Message Turns (Fine-grained turn-by-turn metrics)
CREATE TABLE IF NOT EXISTS message_turns (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    turn_index INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    role TEXT NOT NULL,                        -- 'user', 'assistant', 'system', 'tool'
    model_name TEXT NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_creation_tokens INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0,
    tools_invoked_json TEXT DEFAULT '[]',      -- JSON array of tool names called
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- 4. Subagent Runs (Parent-Child Rollup Linkages)
CREATE TABLE IF NOT EXISTS subagent_runs (
    id TEXT PRIMARY KEY,
    parent_session_id TEXT NOT NULL,
    child_session_id TEXT NOT NULL UNIQUE,
    agent_type TEXT NOT NULL,
    tokens INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (parent_session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (child_session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- 5. Daily Summaries (Pre-aggregated rollups for instant dashboard queries)
CREATE TABLE IF NOT EXISTS daily_summaries (
    date TEXT NOT NULL,                        -- YYYY-MM-DD
    agent_name TEXT NOT NULL,
    project_name TEXT NOT NULL,
    model_name TEXT NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    total_cache_read_tokens INTEGER DEFAULT 0,
    total_cache_creation_tokens INTEGER DEFAULT 0,
    total_cost_usd REAL DEFAULT 0,
    total_duration_seconds REAL DEFAULT 0,
    PRIMARY KEY (date, agent_name, project_name, model_name)
);

-- 6. Pricing Overrides (User-defined custom model rates)
CREATE TABLE IF NOT EXISTS pricing_overrides (
    model_pattern TEXT PRIMARY KEY,            -- Exact name or regex/prefix pattern
    input_cost_per_m REAL NOT NULL,            -- USD per 1M input tokens
    output_cost_per_m REAL NOT NULL,           -- USD per 1M output tokens
    cache_read_cost_per_m REAL DEFAULT 0,      -- USD per 1M cache read tokens
    cache_write_cost_per_m REAL DEFAULT 0,     -- USD per 1M cache write tokens
    source TEXT DEFAULT 'user_override',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Scanner Checkpoints (Fast incremental scan resume)
CREATE TABLE IF NOT EXISTS scanner_checkpoints (
    file_path TEXT PRIMARY KEY,
    last_modified TIMESTAMP NOT NULL,
    file_size INTEGER NOT NULL,
    byte_offset INTEGER NOT NULL,
    line_number INTEGER NOT NULL,
    file_hash TEXT NOT NULL
);

-- 8. Core Performance Indexes
CREATE INDEX IF NOT EXISTS idx_sessions_agent_start ON sessions(agent_name, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_project_start ON sessions(project_name, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_parent ON sessions(parent_session_id) WHERE is_subagent = 1;
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_message_turns_session ON message_turns(session_id, turn_index);
CREATE INDEX IF NOT EXISTS idx_daily_summaries_date ON daily_summaries(date DESC);
```

---

## 5. Agent Transcript Scanning & Parser Specifications

### 5.1 Discovery & Scanner Concurrency Pipeline
1. **Agent Path Registry**: Scans standard locations on startup:
   - `~/.claude/projects/**/*.jsonl`
   - `~/.gemini/antigravity-cli/brain/**/*.jsonl`
   - `~/.gemini/transcripts/*.json`
   - `~/.codex/sessions/**/*.json`
   - `~/.cursor/projects/**/state.vscdb` & transcripts
   - `~/.config/github-copilot/*.log`
   - `~/.opencode/logs/*.jsonl`
   - `~/.hermes/telemetry/*.jsonl`
2. **Worker Pool Concurrency**:
   - `fsnotify` watcher listens for directory modifications.
   - Events are debounced via a 250ms per-file sliding window channel.
   - A bounded pool of `N = min(runtime.NumCPU(), 8)` worker goroutines consumes file change events.
   - Workers query `scanner_checkpoints` to determine if a file has changed (`mtime != saved_mtime || size != saved_size`).
   - If changed, workers read only newly appended bytes starting from `byte_offset`.
   - Parsed records are dispatched to a batch writer channel that commits transactions to SQLite every 100ms or 50 items.

### 5.2 Universal Parser Interface
```go
package parsers

import (
    "io"
    "time"
)

type TokenUsage struct {
    InputTokens         int64
    OutputTokens        int64
    CacheReadTokens     int64
    CacheCreationTokens int64
}

type Turn struct {
    Index     int
    Timestamp time.Time
    Role      string
    Model     string
    Usage     TokenUsage
    Tools     []string
}

type ParsedSession struct {
    ID               string
    AgentName        string
    ProjectName      string
    FilePath         string
    StartTime        time.Time
    EndTime          time.Time
    Model            string
    TotalUsage       TokenUsage
    Turns            []Turn
    IsSubagent       bool
    ParentSessionID  string
    SubagentType     string
    GitBranch        string
    Status           string
}

type AgentParser interface {
    AgentName() string
    Detect(filePath string) bool
    Parse(r io.Reader, startOffset int64) (*ParsedSession, int64, error)
}
```

### 5.3 Agent Parsing Matrix & Normalization Rules

| Agent | File Format | Token Extraction Schema & Rules |
| :--- | :--- | :--- |
| **Claude Code** | JSONL | Extract from `type: "assistant"` lines: `message.usage.input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`. Subagent files detected via parent session directory linkage. |
| **Antigravity CLI** | JSONL | Parse `step_index`, `type: "PLANNER_RESPONSE"`. Usage in `metrics.tokens` or `tool_calls`. Count-once subagent rollups via `parent_conversation_id`. |
| **Gemini CLI** | JSON | Parse `turns[]` with `usageMetadata.promptTokenCount`, `candidatesTokenCount`, `cachedContentTokenCount`. |
| **Codex CLI** | JSON/JSONL | Parse `response.usage.prompt_tokens`, `completion_tokens`. Net calculation: subtract previous cumulative prompt if protocol transmits total context length. |
| **Cursor IDE** | SQLite / JSON | Read `state.vscdb` table `ItemTable` keys `cursorAuth/cachedTokens` and `chatHistory`. |
| **Copilot CLI** | Log / JSON | Parse `[telemetry] request: input_tokens=X, output_tokens=Y`. |
| **Hermes Agent** | JSONL | Read `hermes_telemetry.py` compatible JSONL with task status, tool outcomes, and token usage records. |
| **Pi / Cline / Roo** | JSON / JSONL | Parse custom telemetry blocks with normalized prompt/completion counters. |

---

## 6. Offline Pricing & Cost Engine Specification

### 6.1 Two-Tier Pricing Dataset
1. **Tier 1 (Base Dataset)**: Embedded JSON file (`internal/pricing/pricing_data.json`) generated from `models.dev/api.json` containing 1,000+ public model pricing entries.
2. **Tier 2 (User Overrides)**: Database table `pricing_overrides` queried with priority over Tier 1.

### 6.2 Fuzzy Longest-Prefix Matching
Arbitrary model strings from agent transcripts (e.g. `us.anthropic.claude-3-7-sonnet-20250219-v1:0` or `openai/gpt-4o-2024-08-06`) are normalized:
1. Strip provider prefixes (`anthropic/`, `openai/`, `google/`, `bedrock/`, `us.`).
2. Match against known prefixes ordered by length descending.
3. Fallback to family default (e.g. `claude-3-7-sonnet` -> default Sonnet rate) or zero-cost with a warning.

### 6.3 Cost Calculation Formula
```go
func CalculateCost(usage TokenUsage, rate ModelRate) (grossUSD, netUSD float64) {
    // Gross: Assumes all prompt tokens charged at standard input rate
    totalPrompt := float64(usage.InputTokens + usage.CacheReadTokens + usage.CacheCreationTokens)
    grossUSD = (totalPrompt / 1_000_000.0) * rate.InputCostPerM +
               (float64(usage.OutputTokens) / 1_000_000.0) * rate.OutputCostPerM

    // Net: Accounts for discounted cache reads and cache write premiums
    readRate := rate.CacheReadCostPerM
    if readRate == 0 && rate.InputCostPerM > 0 {
        readRate = rate.InputCostPerM * 0.10 // 90% discount fallback
    }
    writeRate := rate.CacheWriteCostPerM
    if writeRate == 0 && rate.InputCostPerM > 0 {
        writeRate = rate.InputCostPerM * 1.25 // 25% cache write markup fallback
    }

    netUSD = (float64(usage.InputTokens) / 1_000_000.0) * rate.InputCostPerM +
             (float64(usage.CacheReadTokens) / 1_000_000.0) * readRate +
             (float64(usage.CacheCreationTokens) / 1_000_000.0) * writeRate +
             (float64(usage.OutputTokens) / 1_000_000.0) * rate.OutputCostPerM

    return grossUSD, netUSD
}
```

---

## 7. REST API & SSE Streaming Specification

### 7.1 Core Endpoint Catalog

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/healthz` | Health check (`{"status":"ok","version":"1.0.0"}`) |
| `GET` | `/api/sessions` | Paginated sessions (`?page=1&limit=50&agent=&project=&from=&to=`) |
| `GET` | `/api/sessions/{id}` | Detailed session view with turns, subagent runs, and tool usage |
| `GET` | `/api/recent` | Recent 20 sessions for dashboard live feed |
| `GET` | `/api/stats` | Aggregated metrics (total tokens, gross/net cost, active agents) |
| `GET` | `/api/stats/daily` | Time-series daily token & cost breakdowns for Recharts |
| `GET` | `/api/leaderboard` | Top models and top agents by token consumption |
| `GET` | `/api/projects` | Catalog of discovered projects with token/cost aggregates |
| `GET` | `/api/projects/{path...}` | Specific project summary and session list |
| `GET` | `/api/hermes/kanban` | Hermes task status columns and run summaries |
| `GET` | `/api/pricing` | Current resolved model pricing rates |
| `POST` | `/api/pricing/override` | Set custom model price override |
| `GET` | `/events` | Server-Sent Events (SSE) live telemetry stream |

### 7.2 SSE Broker Architecture
The SSE Hub maintains a thread-safe subscriber registry:
- **Keepalive**: Broadcasts a comment heartbeat (`: ping\n\n`) every 15 seconds.
- **Client Channels**: Buffered channel (size: 64) per client. Slow consumers are safely dropped without blocking the scanner worker pool.
- **Events Emitted**:
  - `session.created`: Emitted when a new agent transcript is first detected.
  - `session.updated`: Emitted when new token deltas are parsed for an active session.
  - `scan.progress`: Emitted during full filesystem scan indexing.

---

## 8. Astro Frontend & Go Embedding Integration

### 8.1 Astro Configuration (`frontend/astro.config.mjs`)
```javascript
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  output: 'static',
  outDir: '../internal/web/dist',
  integrations: [
    react(),
    tailwind({ applyBaseStyles: false })
  ],
  vite: {
    server: {
      proxy: {
        '/api': 'http://localhost:8000',
        '/events': 'http://localhost:8000',
        '/healthz': 'http://localhost:8000'
      }
    }
  }
});
```

### 8.2 Go HTTP Asset & SPA Fallback Handler (`internal/web/assets.go`)
```go
package web

import (
    "embed"
    "io/fs"
    "net/http"
    "path"
    "strings"
)

//go:embed all:dist
var distFS embed.FS

func Handler() http.Handler {
    subFS, err := fs.Sub(distFS, "dist")
    if err != nil {
        panic(err)
    }

    fileServer := http.FileServer(http.FS(subFS))

    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        reqPath := path.Clean(r.URL.Path)

        // 1. Static asset caching
        if strings.HasPrefix(reqPath, "/_astro/") || strings.HasPrefix(reqPath, "/assets/") {
            w.Header().Set("Cache-Control", "public, max-age=31536000, immutable")
            fileServer.ServeHTTP(w, r)
            return
        }

        // 2. Check if file exists directly in embed.FS
        f, err := subFS.Open(strings.TrimPrefix(reqPath, "/"))
        if err == nil {
            _ = f.Close()
            w.Header().Set("Cache-Control", "no-cache")
            fileServer.ServeHTTP(w, r)
            return
        }

        // 3. Dynamic route fallbacks for React client islands
        if strings.HasPrefix(reqPath, "/sessions/") {
            r.URL.Path = "/sessions/[id]/index.html"
        } else if strings.HasPrefix(reqPath, "/projects/") {
            r.URL.Path = "/projects/[...path]/index.html"
        } else {
            // Default 404 / root fallback
            r.URL.Path = "/index.html"
        }

        w.Header().Set("Cache-Control", "no-cache")
        fileServer.ServeHTTP(w, r)
    })
}
```

---

## 9. Build, Test, and Packaging Automation

### 9.1 Unified `Makefile`
```makefile
VERSION ?= 1.0.0
COMMIT ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
LDFLAGS = -s -w -X main.Version=$(VERSION) -X main.Commit=$(COMMIT)

.PHONY: all build-frontend build-backend build test clean

all: build

build-frontend:
	@echo "==> Building Astro Static Frontend..."
	cd frontend && npm ci && npm run build

build-backend:
	@echo "==> Compiling Static Go Binary..."
	CGO_ENABLED=0 go build -ldflags="$(LDFLAGS)" -o bin/tokentelemetry ./cmd/tokentelemetry

build: build-frontend build-backend
	@echo "==> Build complete: bin/tokentelemetry"

test:
	go test -v -race ./internal/...

clean:
	rm -rf bin/ internal/web/dist frontend/dist
```

---

## 10. Step-by-Step Autonomous Implementation Roadmap

An autonomous coding agent executing this port must follow these sequential phases:

### Phase 1: Core Foundation & Storage Layer
1. Initialize Go module `github.com/robin-paul/tokentelemetry`.
2. Implement `internal/store` with `modernc.org/sqlite`, connection pool, and `0001_initial.sql` migrations.
3. Add unit tests for SQLite CRUD operations, composite indexes, and concurrency under WAL mode.

### Phase 2: Pricing & Power Engine
1. Embed `pricing_data.json` inside `internal/pricing`.
2. Implement fuzzy longest-prefix model resolver and `CalculateCost` with net/gross cache multipliers.
3. Implement hardware profile electricity cost estimator with fallback defaults.

### Phase 3: Agent Parsers & Scanner Concurrency
1. Implement universal `AgentParser` interface.
2. Implement parsers for all 18+ agent ecosystems (`claude.go`, `antigravity.go`, `gemini.go`, `codex.go`, `cursor.go`, etc.).
3. Implement `internal/scanner/checkpoint.go` and the `fsnotify` + reconciler worker pool in `internal/watcher`.

### Phase 4: REST API Handlers & SSE Broker
1. Implement `internal/events/broker.go` with thread-safe client subscription channels and 15s keepalive pings.
2. Implement `chi` REST routing and 40+ API endpoints in `internal/api/`.
3. Add Bearer token authentication and CORS middleware.

### Phase 5: Astro Frontend Migration & Go Embedding
1. Initialize `frontend/` with Astro static export and `@astrojs/react`.
2. Port React UI components, Recharts visualizations, and Session Inspector scrubber to Astro client islands.
3. Configure `internal/web/assets.go` with `//go:embed all:dist` and SPA fallback routing.

### Phase 6: End-to-End Validation & Verification
1. Run `make build` to verify single-binary compilation.
2. Launch `bin/tokentelemetry --port 8000` and execute integration test verifying live log scanning, SQLite persistence, SSE broadcast, and Web dashboard rendering.
