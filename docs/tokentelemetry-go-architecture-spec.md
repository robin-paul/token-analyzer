# TokenTelemetry Go Single-Module Monorepo & Distributed Telemetry Architecture Specification

**Document Version:** 2.0.0  
**Target System:** TokenTelemetry Go Rewrite (`tokentelemetry-go`)  
**Status:** Canonical Implementation Guide  
**Source Specification Issues:** [#24](https://github.com/robin-paul/token-analyzer/issues/24), [#25](https://github.com/robin-paul/token-analyzer/issues/25), [#26](https://github.com/robin-paul/token-analyzer/issues/26), [#27](https://github.com/robin-paul/token-analyzer/issues/27)  

---

## 1. Executive Summary & Core Architectural Invariants

### 1.1 Purpose
This document specifies the complete target architecture, directory layout, REST ingestion contracts, concurrency models, terminal user interfaces (TUI), and Kubernetes deployment topologies for the **TokenTelemetry Go Single-Module Monorepo**.

The system separates local developer telemetry collection from centralized web/API hosting while maintaining a single unified Go module (`go.mod`):
1. **Collector (`cmd/tt`)**: A lightweight client command-line utility running on developer workstations and CI environments that passively monitors local AI coding agent transcripts, parses token usage, presents a rich interactive terminal interface via Charm's Bubble Tea, and streams ingestion batches over HTTP.
2. **Hub (`cmd/tt-server`)**: A centralized telemetry backend deployed to Kubernetes or server instances that validates ingestion batches, persists sessions in SQLite (WAL mode), recalculates analytical rollups, and serves real-time Server-Sent Events (SSE) alongside an embedded Astro Web dashboard.

### 1.2 Core Architectural Invariants
1. **Single Go Module Monorepo**: All binaries (`cmd/tt`, `cmd/tt-server`) and shared packages (`internal/models`, `internal/parsers`, `internal/pricing`, `internal/client`, etc.) reside within a single Go module at repository root (`github.com/robin-paul/tokentelemetry-go`), eliminating multi-module versioning overhead and `replace` directives.
2. **Clean Seam & Presentation Decoupling**:
   - The CLI Collector (`cmd/tt`) contains no web server or frontend assets, keeping client binary size minimal (~15MB).
   - Ingestion pipelines output to a clean `EventSink` interface, allowing dynamic runtime selection between an interactive Bubble Tea TUI, a headless structured `slog` daemon, or a batch CLI sync command.
3. **Non-Blocking TUI Event Loop**:
   - Bubble Tea’s Elm Architecture event loop (`Update` and `View`) never performs disk I/O, regex parsing, or network calls directly.
   - Background filesystem watcher goroutines and parser worker pools dispatch events into Bubble Tea via thread-safe `tea.Program.Send(msg)` calls.
4. **Idempotent HTTP REST Ingestion & Checkpointing**:
   - Telemetry transfer between Collector and Hub occurs via `POST /api/v1/ingest` with structured `IngestionBatch` JSON payloads.
   - Hub persistence uses atomic SQLite single-writer transactions with `INSERT ... ON CONFLICT(id) DO UPDATE` upserts for sessions and turns, guaranteeing safe replay and duplicate tolerance across network retries.
5. **CGO-Free Pure-Go SQLite**: Use `modernc.org/sqlite` on the Hub to enable cross-compilation across all operating systems (`linux/amd64`, `linux/arm64`, `darwin/amd64`, `darwin/arm64`, `windows/amd64`) without C toolchain dependencies.
6. **Embedded Static Astro Frontend with React Islands**: The Hub embeds pre-rendered static HTML/CSS/JS via Go's `//go:embed all:dist` in `internal/web/assets.go`. High-interactivity components (Analytics charts, Session Inspector turn-scrubber, Hermes Kanban board) hydrate on the client via React 19 islands.
7. **Passive On-Disk Ingestion & Offline Pricing**: Zero MITM proxying of LLM traffic. The system parses logs passively from disk (`fsnotify` + 60s reconciler) and computes financial costs completely offline using an embedded pricing catalog (`internal/pricing/pricing_data.json`).

---

## 2. High-Level Distributed Topology & Monorepo Layout

### 2.1 System Topology

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               DEVELOPER WORKSTATION / CI RUNNER                                │
│                                                                                                │
│  ┌────────────────────────┐   fsnotify    ┌───────────────────────────┐                        │
│  │   Agent Transcripts    │ ────────────► │     Scanner & Parsers     │                        │
│  │ (~/.claude, ~/.cursor) │               │   (Worker Pool & Checkpt) │                        │
│  └────────────────────────┘               └─────────────┬─────────────┘                        │
│                                                         │                                      │
│                                                         ▼                                      │
│                                           ┌───────────────────────────┐                        │
│                                           │   EventSink Dispatcher    │                        │
│                                           └──────┬─────────────┬──────┘                        │
│                                                  │             │                               │
│                      [Interactive TTY]           │             │      [Headless Daemon]        │
│                                                  ▼             ▼                               │
│                                    ┌──────────────────┐  ┌───────────────────┐                 │
│                                    │  Bubble Tea TUI  │  │  slog JSON Logger │                 │
│                                    │ (Lip Gloss Grid) │  │ (stdout / stderr) │                 │
│                                    └──────────────────┘  └───────────────────┘                 │
│                                                  │             │                               │
│                                                  ▼             ▼                               │
│                                    ┌──────────────────────────────────┐                        │
│                                    │      internal/client Ingest      │                        │
│                                    │   (Batch Buffer + Full Jitter)   │                        │
│                                    └──────────────────┬───────────────┘                        │
└───────────────────────────────────────────────────────┼────────────────────────────────────────┘
                                                        │ HTTP POST /api/v1/ingest
                                                        │ Bearer Token / X-TT-Machine-ID
                                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             KUBERNETES TELEMETRY HUB (tt-server)                               │
│                                                                                                │
│  ┌─────────────────────────┐   HTTP / SSE (Single Port :8000)   ┌───────────────────────────┐  │
│  │   Embedded Astro Web    │ ◄────────────────────────────────► │        chi Router         │  │
│  │ (React Client Islands)  │                                    │ & RemoteAuth / CORS MW    │  │
│  └─────────────────────────┘                                    └─────────────┬─────────────┘  │
│                                                                               │                │
│  ┌────────────────────────────────────────────────────────┐                   │                │
│  │                    Events Broker                       │ ◄─────────────────┤                │
│  │      (Real-time SSE Broadcast & Heartbeat Hub)         │                   │                │
│  └──────────────────────────▲─────────────────────────────┘                   ▼                │
│                             │                                   ┌───────────────────────────┐  │
│                             │ Ingestion Events                  │    POST /api/v1/ingest    │  │
│                             └───────────────────────────────────┤      Ingest Handler       │  │
│                                                                 └─────────────┬─────────────┘  │
│                                                                               │                │
│                                                                               ▼                │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                           Pure-Go SQLite Engine (WAL Mode)                               │  │
│  │  ┌──────────────────────────────────────────┐  ┌──────────────────────────────────────┐  │  │
│  │  │   Dedicated Single-Writer Connection     │  │   Multi-Connection Read Pool         │  │  │
│  │  │   (SetMaxOpenConns(1) / Serialized Tx)   │  │   (SetMaxOpenConns(2 * NumCPU))      │  │  │
│  │  └──────────────────────────────────────────┘  └──────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Go Monorepo Directory Structure

```
repositories/tokentelemetry-go/
├── cmd/
│   ├── tt/                         # Client CLI Collector binary
│   │   ├── main.go                 # Cobra command tree entrypoint
│   │   ├── watch.go                # tt watch (TUI or daemon)
│   │   ├── scan.go                 # tt scan (one-off sweep)
│   │   ├── config.go               # tt config get/set
│   │   ├── status.go               # tt status
│   │   └── send.go                 # tt send (test injection)
│   └── tt-server/                  # Central Telemetry Hub server binary
│       └── main.go                 # Hub entrypoint: flags, DB init, chi router, web handler
├── internal/
│   ├── api/                        # Hub REST API handlers & middleware
│   │   ├── router.go               # chi router registration & SPA fallback
│   │   ├── middleware.go           # Bearer auth, CORS, logging, gzip recovery
│   │   ├── ingest.go               # POST /api/v1/ingest handler
│   │   ├── sessions.go             # /api/sessions, /api/recent
│   │   ├── stats.go                # /api/stats, /api/stats/daily, /api/leaderboard
│   │   ├── projects.go             # /api/projects
│   │   ├── hermes.go               # /api/hermes/* handlers
│   │   ├── config.go               # /api/config, /api/settings, /api/pricing
│   │   ├── system.go               # /healthz, /version
│   │   └── server.go               # Server struct and lifecycle
│   ├── client/                     # Collector HTTP client & batch buffer
│   │   ├── ingest.go               # HTTP client with retry, full jitter, machine metadata
│   │   └── buffer.go               # Bounded batching channel buffer (50 items / 500ms)
│   ├── collector/                  # Collector engine & presentation decoupling
│   │   ├── pipeline.go             # Watcher + Parser + Ingest Coordinator
│   │   ├── sink.go                 # EventSink interface (TUISink vs SlogSink)
│   │   └── config.go               # Collector config file parser (~/.tokentelemetry/config.yaml)
│   ├── tui/                        # Charm Bubble Tea interactive TUI
│   │   ├── model.go                # tea.Model state machine, Update loop, keymaps
│   │   ├── view.go                 # Lip Gloss responsive layout renderer (KPIs, table, header)
│   │   ├── styles.go               # Color palette & Lip Gloss style definitions
│   │   └── runner.go               # tea.Program initialization and terminal lifecycle
│   ├── events/                     # Real-time event streaming & SSE
│   │   ├── broker.go               # Central thread-safe SSE subscriber hub
│   │   └── messages.go             # SSE event payloads (session.new, session.update, stats.updated)
│   ├── scanner/                    # Agent transcript scanning & parser engine
│   │   ├── engine.go               # Orchestrator, worker pool, discovery manager
│   │   ├── checkpoint.go           # File state tracking (mtime, size, byte offset)
│   │   └── parsers/                # 18+ Agent-specific parser implementations
│   │       ├── parser.go           # AgentParser interface & data types
│   │       ├── claude.go           # Claude Code parser
│   │       ├── codex.go            # Codex CLI parser
│   │       ├── gemini.go           # Gemini CLI parser
│   │       ├── antigravity.go      # Antigravity CLI parser
│   │       ├── cursor.go           # Cursor IDE SQLite / state.vscdb parser
│   │       ├── copilot.go          # GitHub Copilot CLI & VS Code parser
│   │       ├── opencode.go         # OpenCode parser
│   │       ├── hermes.go           # Hermes autonomous agent telemetry parser
│   │       └── ...                 # Cline, Roo, Pi, Grok, DSH, MetaMuse, SmallCode, Windsurf
│   ├── watcher/                    # Log filesystem watcher
│   │   ├── watcher.go              # fsnotify directory watcher & debouncing
│   │   └── reconciler.go           # Periodic fallback reconciler
│   ├── pricing/                    # Offline pricing engine & cost calculator
│   │   ├── engine.go               # Pricing calculation, cache multipliers
│   │   ├── dataset.go              # Embedded models.dev pricing table loader
│   │   ├── resolver.go             # Fuzzy longest-prefix model resolver
│   │   ├── power.go                # Hardware profile power/electricity estimator
│   │   └── pricing_data.json       # Embedded catalog of 1,000+ public model rates
│   ├── store/                      # Pure-Go SQLite persistence layer
│   │   ├── db.go                   # Single-writer connection & WAL pragmas
│   │   ├── migrator.go             # Embedded SQL migration runner
│   │   ├── migrations/             # SQL migration files
│   │   │   ├── 0001_initial.sql
│   │   │   ├── 0002_indexes.sql
│   │   │   └── 0003_collector_ingest.sql
│   │   ├── sessions.go             # Session & message turn queries / upserts
│   │   ├── summaries.go            # Daily summary rollups & aggregations
│   │   └── checkpoints.go          # Scanner checkpoint persistence
│   ├── models/                     # Shared domain entities
│   │   ├── session.go              # Session, MessageTurn, SubagentRun
│   │   ├── ingest.go               # IngestionBatch, ClientMetadata, IngestionResponse
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
│   │   ├── layouts/                # BaseLayout.astro
│   │   ├── pages/                  # Static routes (index.astro, analytics, sessions, etc.)
│   │   ├── components/             # React Client Islands (Inspector, Charts, Kanban)
│   │   └── lib/                    # API client & formatting utilities
├── deploy/                         # Production & Kubernetes deployments
│   ├── Dockerfile                  # Multi-stage Hub build (Node Astro + Pure-Go binary)
│   └── k8s/                        # Kubernetes manifests
│       ├── deployment.yaml
│       ├── service.yaml
│       └── pvc.yaml
├── Makefile                        # Unified build, test, and release targets
└── go.mod                          # Single Go module definition
```

---

## 3. HTTP Ingestion REST API & Persistence Specification

### 3.1 REST Endpoint: `POST /api/v1/ingest`
- **Path**: `/api/v1/ingest`
- **Method**: `POST`
- **Headers**:
  - `Content-Type: application/json`
  - `Authorization: Bearer <token>` (Constant-time verified via `crypto/subtle.ConstantTimeCompare`)
  - `X-TT-Machine-ID: <uuid>` (Collector machine identifier)
  - `X-TT-Client-Version: <semver>`
  - `X-TT-Batch-ID: <uuid>`

### 3.2 Request Schema (`IngestionBatch`)
```go
package models

import "time"

type ClientMetadata struct {
    MachineID     string    `json:"machine_id"`
    Hostname      string    `json:"hostname"`
    ClientVersion string    `json:"client_version"`
    User          string    `json:"user,omitempty"`
    OS            string    `json:"os,omitempty"`
    SentAt        time.Time `json:"sent_at"`
    BatchID       string    `json:"batch_id"`
}

type IngestionBatch struct {
    Metadata ClientMetadata `json:"metadata"`
    Sessions []Session      `json:"sessions"`
}

type IngestionResponse struct {
    Status           string    `json:"status"`
    BatchID          string    `json:"batch_id"`
    AcceptedSessions int       `json:"accepted_sessions"`
    AcceptedTurns    int       `json:"accepted_turns"`
    RejectedSessions int       `json:"rejected_sessions"`
    Errors           []string  `json:"errors,omitempty"`
    ServerTime       time.Time `json:"server_time"`
}
```

### 3.3 Hub Persistence & Idempotency Semantics
1. **Machine Scoping**: Sessions are tagged with `machine_id` (`0003_collector_ingest.sql`). Composite index `idx_sessions_machine_agent ON sessions(machine_id, agent_name, start_time DESC)`.
2. **Session Upsert**:
   ```sql
   INSERT INTO sessions (
       id, session_id, agent_name, project_name, file_path, machine_id,
       created_at, updated_at, start_time, end_time, duration_seconds,
       model_raw, model_resolved, input_tokens, output_tokens,
       cache_read_tokens, cache_creation_tokens, gross_cost_usd, net_cost_usd,
       electricity_cost_usd, hardware_profile, status, git_branch,
       is_subagent, parent_session_id, subagent_type
   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
   ON CONFLICT(id) DO UPDATE SET
       updated_at = excluded.updated_at,
       end_time = excluded.end_time,
       duration_seconds = excluded.duration_seconds,
       model_raw = excluded.model_raw,
       model_resolved = excluded.model_resolved,
       input_tokens = excluded.input_tokens,
       output_tokens = excluded.output_tokens,
       cache_read_tokens = excluded.cache_read_tokens,
       cache_creation_tokens = excluded.cache_creation_tokens,
       gross_cost_usd = excluded.gross_cost_usd,
       net_cost_usd = excluded.net_cost_usd,
       electricity_cost_usd = excluded.electricity_cost_usd,
       status = excluded.status,
       git_branch = excluded.git_branch;
   ```
3. **Turn Replacement**: Existing turns for updated sessions are deleted and replaced atomically within the single-writer transaction to guarantee zero duplicate turns.
4. **Summary Recalculation**: `db.RollupDailySummariesForDate(ctx, date)` runs immediately after transaction commit for all affected dates in the batch.
5. **Real-Time SSE Propagation**: Hub dispatches `session.created` (new sessions), `session.updated` (modified sessions), and `stats.updated` events to connected browser tabs.

---

## 4. Collector CLI & Cobra Architecture (`cmd/tt`)

### 4.1 Command Matrix

| Command | Arguments / Flags | Description |
| :--- | :--- | :--- |
| `tt watch` *(default)* | `[paths...]`, `--hub`, `--api-key`, `--daemon`, `--log-level` | Monitor transcript directories. Runs interactive Bubble Tea TUI on TTY, or structured `slog` daemon when `--daemon` or non-TTY. |
| `tt scan` | `[paths...]`, `--hub`, `--api-key`, `--dry-run` | One-off discovery sweep of transcript directories, parsing all sessions and streaming sync batch to Hub. |
| `tt config` | `get [key]`, `set [key] [val]`, `list` | Inspect and edit local collector configuration in `~/.tokentelemetry/config.yaml`. |
| `tt status` | `--hub`, `--api-key` | Ping configured Hub server, print connectivity health, active watchers, and local queue stats. |
| `tt send` | `--file <path>`, `--agent <name>` | Inject a synthetic transcript file for end-to-end integration and verification testing. |

### 4.2 Configuration Precedence
1. Explicit CLI Flags (`--hub`, `--api-key`, `--scan-dir`).
2. Environment Variables (`TT_HUB_URL`, `TT_AUTH_TOKEN`, `TT_SCAN_DIR`).
3. User Configuration File (`~/.tokentelemetry/config.yaml`).
4. Hardcoded Defaults (`hub: http://localhost:8000`, standard agent directories).

---

## 5. Interactive Bubble Tea TUI Architecture (`internal/tui`)

### 5.1 Presentation Decoupling & Non-Blocking Invariant
The presentation layer is decoupled via the `collector.EventSink` interface:
- **`TUISink`**: Dispatches incoming turns and session events to Bubble Tea using thread-safe `tea.Program.Send(TurnIngestedMsg{...})`.
- **`SlogSink`**: Writes structured JSON or text log lines to stdout when running in headless daemon mode.

### 5.2 Layout Breakdown (Lip Gloss)
```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│  ⚡ TOKEN TELEMETRY COLLECTOR        ● HUB: ONLINE (http://k8s-tt:8000)         UPTIME: 1h 24m │
├────────────────────────────────┬───────────────────────────────┬───────────────────────────────┤
│ THROUGHPUT                     │ CACHE EFFICIENCY              │ ESTIMATED COST                │
│ 1,420.5 tok/s                  │ 68.4% Hit Rate                │ $14.82 Net                    │
│ 42 turns ingested              │ 1.2M tokens saved             │ $22.40 Gross (Est)            │
├────────────────────────────────┴───────────────────────────────┴───────────────────────────────┤
│ TIME      AGENT       PROJECT             MODEL                 IN / OUT / CACHE          COST │
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 14:02:11  claude_code token-analyzer      claude-3-7-sonnet     125000 / 4200 / 850000  $0.1245│
│ 14:02:18  codex       fintech-platform    o3-mini               4510 / 890 / 0          $0.0180│
│ 14:02:25  cursor      react-dashboard     claude-3-5-sonnet     890 / 240 / 16384       $0.0080│
│ 14:02:30  hermes      db-optimizer        deepseek-r1           12400 / 1200 / 0        $0.0320│
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [q] quit  [c] clear  [p] pause  [↑/↓] scroll viewport                                          │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Responsive Breakpoint Adaptations
- **Wide ($\ge 120$ cols)**: 3-column KPI cards, full model name strings, detailed token breakdown.
- **Medium ($80-119$ cols)**: 2-column KPI cards, consolidated token counts (`In/Out/Cache`), truncated project basenames.
- **Narrow ($< 80$ cols)**: Stacked KPI banner, truncated model strings (`claude-3-7...`), compact status indicators.

---

## 6. Production Packaging & Kubernetes Deployment

### 6.1 Multi-Stage `Dockerfile` (`deploy/Dockerfile`)
```dockerfile
# Stage 1: Build Astro Static Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Compile Pure-Go Hub Binary
FROM golang:1.24-alpine AS backend-builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
COPY --from=frontend-builder /app/internal/web/dist ./internal/web/dist
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /bin/tt-server ./cmd/tt-server

# Stage 3: Minimal Production Image
FROM alpine:3.20
RUN apk --no-cache add ca-certificates tzdata
WORKDIR /app
COPY --from=backend-builder /bin/tt-server /usr/local/bin/tt-server
EXPOSE 8000
VOLUME ["/data"]
ENV TT_DB_PATH=/data/tokentelemetry.db
ENTRYPOINT ["/usr/local/bin/tt-server", "--db", "/data/tokentelemetry.db", "--port", "8000"]
```

### 6.2 Kubernetes Deployment & PVC Manifests (`deploy/k8s/`)

#### PersistentVolumeClaim (`deploy/k8s/pvc.yaml`)
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: tokentelemetry-data
  namespace: telemetry
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

#### Deployment & Service (`deploy/k8s/deployment.yaml`)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tokentelemetry-hub
  namespace: telemetry
  labels:
    app: tokentelemetry-hub
spec:
  replicas: 1  # Single replica for SQLite WAL single-writer architecture
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: tokentelemetry-hub
  template:
    metadata:
      labels:
        app: tokentelemetry-hub
    spec:
      containers:
        - name: hub
          image: ghcr.io/robin-paul/tokentelemetry-hub:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8000
              name: http
          env:
            - name: TT_AUTH_TOKEN
              valueFrom:
                secretKeyRef:
                  name: tokentelemetry-secrets
                  key: auth-token
                  optional: true
          volumeMounts:
            - name: data-volume
              mountPath: /data
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /healthz
              port: 8000
            initialDelaySeconds: 2
            periodSeconds: 5
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "1000m"
              memory: "512Mi"
      volumes:
        - name: data-volume
          persistentVolumeClaim:
            claimName: tokentelemetry-data
---
apiVersion: v1
kind: Service
metadata:
  name: tokentelemetry-hub
  namespace: telemetry
spec:
  type: ClusterIP
  selector:
    app: tokentelemetry-hub
  ports:
    - port: 8000
      targetPort: 8000
      name: http
```

---

## 7. Unified Makefile Targets

```makefile
VERSION ?= 1.0.0
COMMIT ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
LDFLAGS = -s -w -X main.Version=$(VERSION) -X main.Commit=$(COMMIT)

.PHONY: all build-frontend build-server build-cli build-all test clean docker-build

all: build-all

build-frontend:
	@echo "==> Building Astro Static Frontend..."
	cd frontend && npm ci && npm run build

build-server: build-frontend
	@echo "==> Compiling Hub Server Binary (bin/tt-server)..."
	CGO_ENABLED=0 go build -ldflags="$(LDFLAGS)" -o bin/tt-server ./cmd/tt-server

build-cli:
	@echo "==> Compiling Collector CLI Binary (bin/tt)..."
	CGO_ENABLED=0 go build -ldflags="$(LDFLAGS)" -o bin/tt ./cmd/tt

build-all: build-server build-cli
	@echo "==> Successfully built bin/tt and bin/tt-server"

test:
	go test -v -race ./internal/...

docker-build:
	docker build -t tokentelemetry-hub:$(VERSION) -f deploy/Dockerfile .

clean:
	rm -rf bin/ internal/web/dist frontend/dist
```

---

## 8. Phased Implementation Roadmap

The execution tickets for this architecture proceed sequentially:

### Phase 1: Ingestion API & Client Buffer ([#28](https://github.com/robin-paul/token-analyzer/issues/28))
1. Implement `models.IngestionBatch`, `models.ClientMetadata`, and `models.IngestionResponse` in `internal/models/ingest.go`.
2. Add migration `0003_collector_ingest.sql` adding `machine_id` to `sessions`.
3. Implement `POST /api/v1/ingest` in `internal/api/ingest.go` with single-writer upserts and SSE broadcast.
4. Implement `internal/client/ingest.go` and `internal/client/buffer.go` with dual-trigger batching and full-jitter retries.

### Phase 2: Cobra Command Tree in `cmd/tt` ([#29](https://github.com/robin-paul/token-analyzer/issues/29))
1. Scaffold `cmd/tt` with Cobra root command and subcommands (`watch`, `scan`, `config`, `status`, `send`).
2. Implement configuration loader for `~/.tokentelemetry/config.yaml`.
3. Implement `collector.RunHeadless` daemon mode with structured `slog`.

### Phase 3: Charm Bubble Tea TUI Monitor ([#30](https://github.com/robin-paul/token-analyzer/issues/30))
1. Implement `internal/tui/model.go` state machine with `table.Model`, metrics accumulators, and keybindings.
2. Implement Lip Gloss responsive layout renderer in `internal/tui/view.go`.
3. Wire `TUISink` with `tea.Program.Send` to stream live turns into the terminal.

### Phase 4: Packaging, Makefile & Kubernetes Manifests ([#31](https://github.com/robin-paul/token-analyzer/issues/31))
1. Rename/refactor `cmd/tokentelemetry` $\rightarrow$ `cmd/tt-server`.
2. Update `Makefile` with `build-cli`, `build-server`, and `build-all`.
3. Author `deploy/Dockerfile` and `deploy/k8s/` manifests.
4. Write end-to-end integration test validating `bin/tt` streaming into `bin/tt-server`.
