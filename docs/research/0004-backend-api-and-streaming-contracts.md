# Backend API Surface and Real-Time Event Streaming Contracts

**Document ID:** `0004-backend-api-and-streaming-contracts`  
**Related Ticket:** Wayfinder Research Ticket #4 (Part of Map #1)  
**Target Codebase:** `repositories/tokentelemetry/backend/`  
**Status:** Complete  

---

## 1. Executive Summary & Architectural Overview

The TokenTelemetry backend is implemented as a **FastAPI** application running in Python ([`repositories/tokentelemetry/backend/main.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L171)), typically served by Uvicorn on port `8000` (or configured via `TT_API_PORT` / `--port`).

### Key Operational Characteristics:
1. **Passive Log/Disk Scanner Architecture**: Rather than acting as an active proxy intercepting live LLM requests, TokenTelemetry functions primarily as an on-disk scanner and aggregator across 17+ coding agents and harnesses (Claude Code, Codex, Gemini CLI, Antigravity, Qwen Code, Cursor, Copilot CLI / VS Code, OpenCode, Hermes, Grok Build, Pi Coding Agent, Cline, Meta Muse, Prime Agent, SmallCode, DeepSeek Harness `dsh`, etc.).
2. **State & Caching Layer**:
   - **In-Memory Cache**: 30-second TTL scan cache for full session lists ([`main.py:L7480-7486`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L7480-L7486)).
   - **Parse Cache (Sidecar)**: Mtime-keyed JSON parse cache under `~/.tokentelemetry/cache/<agent>/<session_id>.json` ([`scan_cache.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/scan_cache.py#L63-L64)).
   - **Durable History Store**: SQLite database `~/.tokentelemetry/history.db` ([`history_store.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/history_store.py#L50-L120)) providing tiered retention (`sessions` rollup table, `transcripts` compressed blob table, `summaries` table).
   - **Notification Center**: SQLite database `~/.tokentelemetry/notifications.db` ([`notifications.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/notifications.py#L30-L60)) managing live, unread, toasted, and cleared alert states.
   - **Trace Summaries Store**: SQLite database `~/.tokentelemetry/summaries.db` ([`summaries.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/summaries.py#L21-L32)).
   - **JSON Configs**: Atomically updated files for `aliases.json`, `hidden.json`, `budgets.json`, `preferences.json`, `power.json`, `retention.json`, `billing.json`, `billing_plans.json`, and `summarizer.json` in `~/.tokentelemetry/`.
3. **No Active WebSockets or SSE in Current Backend**:
   - **Event Streaming Contract Analysis**: Neither Server-Sent Events (`text/event-stream`) nor WebSockets (`ws://` / `wss://`) are currently implemented in the FastAPI backend or consumed by the Next.js frontend.
   - **Dashboard Real-Time Strategy**: The dashboard achieves pseudo-real-time updates via client-side periodic polling (implemented via `useResource` in [`frontend/src/lib/api.ts:L159-L184`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/frontend/src/lib/api.ts#L159-L184) using `setInterval` with a customizable `pollMs`).
   - **Outbound Event Emitting**: Product telemetry uses fire-and-forget background HTTP POST requests to an external Cloudflare Worker proxy ([`telemetry.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/telemetry.py#L52-L68)).

---

## 2. Authentication, CORS, and Middleware Architecture

### 2.1 Remote Access Authentication Gate (`RemoteAuthMiddleware`)
- **Location**: [`main.py:L202-L250`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L202-L250)
- **Mechanism**:
  - Gated when environment variable `TT_AUTH_TOKEN` is present and non-empty.
  - **Loopback Exemption**: All loopback connections (`127.0.0.1`, `::1`, `localhost`, and `::ffff:127.0.0.1`) bypass authentication automatically.
  - **Token Presentation**: Non-loopback requests must present the token either via `Authorization: Bearer <token>` HTTP header or via `?token=<token>` query string parameter (the latter is specifically supported for browser-native `<img>`/`<a>` media requests from `/artifacts`).
  - **Verification**: Constant-time comparison using `hmac.compare_digest`.
  - **Error Response**: `401 Unauthorized` with JSON `{"detail": "Remote access requires an access token.", "auth": "token"}`.

### 2.2 CORS Policy
- **Location**: [`main.py:L180-L187`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L180-L187), [`main.py:L251-L257`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L251-L257)
- **Regex**: `^https?://(localhost|127\.0\.0\.1|<TT_ALLOWED_ORIGINS>):\d+$`
- **Settings**: `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`.

---

## 3. Comprehensive HTTP REST Endpoint Catalog

### 3.1 System, Core & Discovery Endpoints

#### `GET /`
- **Location**: [`main.py:L2850-L2852`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L2850-L2852)
- **Description**: Health check endpoint.
- **Request Parameters**: None.
- **Response Model**: `200 OK`
  ```json
  {
    "message": "TokenTelemetry API is running"
  }
  ```

#### `GET /version`
- **Location**: [`main.py:L2805-L2848`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L2805-L2848)
- **Description**: Compares local git HEAD against remote GitHub main repository, reporting whether the instance is behind and providing release notes / update highlights.
- **Request Parameters**: None.
- **Response Model**: `200 OK`
  ```json
  {
    "current": "abc1234567890abcdef1234567890abcdef12345",
    "latest": "def1234567890abcdef1234567890abcdef12345",
    "behind": false,
    "releases": [
      {
        "tag": "v1.2.0",
        "title": "v1.2.0 Release Title",
        "highlights": [
          {
            "title": "Feature name",
            "description": "Optional description",
            "href": "https://..."
          }
        ]
      }
    ],
    "latest_release": "v1.2.0|v1.2.0 Release Title",
    "release_url": "https://github.com/VasiHemanth/tokentelemetry",
    "source": "cache | github | disabled | offline | none",
    "repo": "VasiHemanth/tokentelemetry"
  }
  ```

#### `GET /agents`
- **Location**: [`main.py:L2884-L2886`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L2884-L2886)
- **Description**: Enumerates detected coding agents present on disk.
- **Request Parameters**: None.
- **Response Model**: `200 OK`
  ```json
  ["claude", "codex", "gemini", "antigravity", "qwen", "cursor", "copilot", "opencode", "hermes", "grok", "pi", "cline", "muse", "prime", "dsh", "smallcode"]
  ```

#### `GET /remote-access`
- **Location**: [`main.py:L7505-L7521`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L7505-L7521)
- **Description**: Returns remote access connection pairing URL and bootstrap token. Strictly restricted to loopback callers; remote callers receive `403 Forbidden`.
- **Response Model**: `200 OK`
  ```json
  {
    "enabled": true,
    "url": "http://192.168.1.100:3000/?token=secret_token",
    "token": "secret_token"
  }
  ```
  *(Or `{"enabled": false}` if not configured).*

#### `GET /pricing`
- **Location**: [`main.py:L7499-L7503`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L7499-L7503)
- **Description**: Returns canonical pricing table and update timestamp.
- **Response Model**: `200 OK`
  ```json
  {
    "updated": "2026-05-17",
    "models": {
      "claude-sonnet-4-6": {
        "in": 3.00,
        "out": 15.00,
        "cached_read": 0.30
      }
    }
  }
  ```

---

### 3.2 Sessions, Traces, Subagents & Artifacts

#### `GET /sessions`
- **Location**: [`main.py:L7488-L7497`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L7488-L7497)
- **Description**: Returns the complete list of scanned sessions across all detected agents.
- **Query Parameters**:
  - `fresh` (bool, default `False`): Force bypass of the in-RAM 30s cache.
- **Response Model**: `200 OK` (Array of session objects):
  ```json
  [
    {
      "id": "session-uuid",
      "agent": "claude",
      "project": "/path/to/project",
      "timestamp": "2026-08-21T10:00:00+00:00",
      "model": "claude-sonnet-4-6",
      "provider": "anthropic",
      "endpoint": null,
      "billing_mode": "subscription",
      "tokens": {
        "input": 12000,
        "output": 1500,
        "cached": 8000,
        "total": 13500,
        "_cached_sum": 24000
      },
      "cost": 0.045,
      "tok_per_sec": 35.2,
      "has_plan": false,
      "subagents": [],
      "mcp_tools": ["mcp__fetch"],
      "skills_used": [{"name": "research", "count": 2}],
      "mcp_usage": {"fetch-server": {"fetch": 3}},
      "delegation": {
        "spawn_count": 1,
        "linked_children": 1,
        "by_type": {}
      },
      "loop": null,
      "published_artifacts": []
    }
  ]
  ```

#### `GET /sessions/{session_id}`
- **Location**: [`main.py:L7738-L8530`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L7738-L8530)
- **Description**: Returns normalized chronological trace events for a specific session.
- **Path Parameters**: `session_id` (str)
- **Query Parameters**: `agent` (str, required)
- **Response Model**: `200 OK` (Array of normalized event objects or structured object depending on agent format).
  - Normal format (Claude/Codex/Pi/Muse/DSH/Cline/etc.):
    ```json
    [
      {
        "type": "user | assistant | tool_call | tool_result | assistant_thinking | session_meta",
        "normalized_timestamp": 1787310000000.0,
        "timestamp": "2026-08-21T10:00:00Z",
        "message": {
          "role": "user | assistant",
          "content": [
            {"type": "text", "text": "Prompt"},
            {"type": "thinking", "thinking": "..."},
            {"type": "tool_use", "id": "call_1", "name": "view_file", "input": {}},
            {"type": "tool_result", "tool_use_id": "call_1", "content": "..."}
          ]
        },
        "payload": { ... }
      }
    ]
    ```
  - Antigravity / Gemini CLI structured format:
    ```json
    {
      "sessionId": "session-uuid",
      "projectHash": "",
      "kind": "antigravity_cli | antigravity_brain | antigravity_logs",
      "startTime": "2026-08-21T10:00:00Z",
      "lastUpdated": "2026-08-21T10:30:00Z",
      "messages": [ ... ]
    }
    ```
  - Error: `{"error": "Not found"}` or `{"error": "Invalid agent"}`.

#### `GET /sessions/{session_id}/subagents/{agent_id}/trace`
- **Location**: [`main.py:L8555-L8596`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L8555-L8596)
- **Description**: Returns the raw trace events for an embedded subagent transcript (specifically Claude, Cursor, Muse).
- **Path Parameters**: `session_id` (str), `agent_id` (str)
- **Query Parameters**: `agent` (str, required)
- **Response Model**: `200 OK` (JSON array of trace events) or `{"error": "..."}`.

#### `GET /sessions/{session_id}/delegation`
- **Location**: [`main.py:L8598-L8650`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L8598-L8650)
- **Description**: Breakdown of subagent delegation and child tasks spawned by a session.
- **Path Parameters**: `session_id` (str)
- **Query Parameters**: `agent` (str, required)
- **Response Model**: `200 OK`
  ```json
  {
    "supported": true,
    "tokens_recorded": true,
    "spawn_count": 2,
    "subagents": [
      {
        "agent_id": "sub_123",
        "agent_type": "researcher",
        "tokens": {"input": 4000, "output": 800, "total": 4800},
        "cost": 0.015
      }
    ],
    "totals": {"input": 8000, "output": 1600, "total": 9600},
    "cost": 0.030
  }
  ```

#### `GET /sessions/{session_id}/grok-forensics`
- **Location**: [`main.py:L1896-L2016`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L1896-L2016)
- **Description**: Rich telemetry forensics payload for Grok Build sessions (tool lifecycles, phase changes, permission resolutions, token progression, accurate signals).
- **Path Parameters**: `session_id` (str)
- **Response Model**: `200 OK`
  ```json
  {
    "session_id": "uuid",
    "summary": {},
    "plan_mode": {},
    "signals": {
      "context_tokens_used": 45000,
      "context_window_tokens": 256000,
      "context_window_usage_pct": 17.5,
      "tool_call_count": 42,
      "tools_used": ["view_file", "grep_search"],
      "models_used": ["grok-build-0.1"],
      "session_duration_seconds": 320,
      "turn_count": 14,
      "user_message_count": 3,
      "assistant_message_count": 11,
      "error_count": 0,
      "tool_failure_count": 0,
      "cancellation_count": 0,
      "compaction_count": 0,
      "doom_loop_detections": 0,
      "agent_lines_added": 120,
      "agent_lines_removed": 15,
      "agent_files_touched": 4,
      "avg_time_to_first_token_ms": 420.5,
      "avg_response_time_ms": 1100.0
    },
    "tool_events": [],
    "permission_events": [],
    "phase_events": [],
    "token_progression": [],
    "counts": {
      "tools": 42,
      "permissions": 0,
      "phases": 2,
      "token_samples": 14
    }
  }
  ```

#### `GET /sessions/{session_id}/hermes-overlay`
- **Location**: [`main.py:L2037-L2050`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L2037-L2050)
- **Description**: Hermes log summary and memory I/O telemetry overlay.
- **Path Parameters**: `session_id` (str)
- **Response Model**: `200 OK`
  ```json
  {
    "session_id": "sid",
    "profile": "default",
    "log_coverage": "full | partial | not_captured",
    "performance": {}
  }
  ```

#### `GET /artifacts` and `HEAD /artifacts`
- **Location**: [`main.py:L7523-L7556`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L7523-L7556)
- **Description**: Securely streams a local artifact file (image, markdown, HTML, video) located within known allowed agent data trees.
- **Query Parameters**:
  - `path` (str, required): Absolute file path to stream.
  - `token` (str, optional): Auth token for non-loopback clients.
- **Response**: File content with appropriate `Content-Type` header (via Starlette `FileResponse`).
- **Security Guardrail**: Verifies `resolved.is_relative_to(allowed_dir)` against allowlist (`CLAUDE_DIR`, `CODEX_DIR`, `GEMINI_DIR`, `ANTIGRAVITY_BRAIN_DIRS`, `CURSOR_DIR`, `VSCODE_BASE`, etc.). Returns `403 Forbidden` if unauthorized or missing.

---

### 3.3 Analytics & Projects

#### `GET /analytics`
- **Location**: [`main.py:L9930-L10199`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9930-L10199)
- **Description**: Multi-dimensional token usage, cost, energy, cloud savings, CO2, skill, MCP, subagent, and recurring loop attribution metrics across specified date ranges.
- **Query Parameters**:
  - `from` (`from_`, str, optional): Lower date boundary (YYYY-MM-DD or UTC ISO).
  - `to` (str, optional): Upper date boundary (YYYY-MM-DD or UTC ISO).
  - `granularity` (str, default `"day"`): Date bucket resolution (`"day"`, `"week"`, `"month"`).
  - `agents` (List[str], optional): Array of agent filter names.
  - `models` (List[str], optional): Array of model filter names.
  - `projects` (List[str], optional): Array of project directory path filters.
- **Response Model**: `200 OK`
  ```json
  {
    "by_agent": {
      "claude": {
        "input": 100000,
        "output": 15000,
        "cached": 80000,
        "cache_reads": 150000,
        "total": 115000,
        "cost": 0.45,
        "energy_wh": 0.0,
        "savings_usd": 0.0,
        "co2_g": 0.0,
        "session_count": 10,
        "cache_hit_pct": 60.0
      }
    },
    "by_day": [
      {
        "date": "2026-08-21",
        "total": 115000,
        "input": 100000,
        "output": 15000,
        "cached": 80000,
        "cost": 0.45,
        "energy_wh": 0.0,
        "savings_usd": 0.0,
        "co2_g": 0.0
      }
    ],
    "by_model": {},
    "by_skill": {},
    "by_mcp_server": {},
    "by_subagent_type": {},
    "by_loop": {},
    "loops": {},
    "delegation": {},
    "total": {
      "input": 100000,
      "output": 15000,
      "cached": 80000,
      "total": 115000,
      "cost": 0.45,
      "energy_wh": 0.0,
      "savings_usd": 0.0,
      "co2_g": 0.0,
      "cache_hit_pct": 60.0
    },
    "coverage": {},
    "granularity": "day",
    "pricing_updated": "2026-05-17"
  }
  ```

#### `GET /projects`
- **Location**: [`main.py:L8915-L9094`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L8915-L9094)
- **Description**: Returns all project workspaces discovered from session logs, grouped with git worktrees and synthesized parent repositories.
- **Query Parameters**:
  - `include_hidden` (bool, default `False`): Include user-hidden projects.
- **Response Model**: `200 OK` (Array of project objects):
  ```json
  [
    {
      "name": "token-analyzer",
      "path": "/Users/.../Proj/token-analyzer",
      "session_count": 15,
      "agents": ["claude", "codex"],
      "mcp_tools": ["fetch"],
      "subagent_count": 3,
      "configured_subagent_count": 2,
      "plan_count": 1,
      "tokens": {
        "input": 200000,
        "output": 30000,
        "cached": 100000,
        "total": 230000,
        "cost": 1.25
      },
      "plans": [],
      "artifacts": [],
      "status": "active | missing",
      "hidden": false,
      "canonical_repo": "/Users/.../Proj/token-analyzer",
      "is_worktree": false,
      "is_repo_root": true,
      "worktrees": [],
      "aggregate": { ... }
    }
  ]
  ```

---

### 3.4 Budgets & Notification Center

#### `GET /budgets`
- **Location**: [`main.py:L9787-L9791`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9787-L9791)
- **Description**: Evaluates and returns all observational spend and token budgets against the session window, computing percentage used and alert levels.
- **Response Model**: `200 OK`
  ```json
  {
    "budgets": [
      {
        "id": "uuid",
        "filters": {"project": "/path", "agent": "claude"},
        "period": "monthly | weekly | rolling_30d",
        "limit_type": "usd | tokens",
        "limit_value": 50.0,
        "thresholds": [0.8, 1.0],
        "enabled": true,
        "used": 42.5,
        "fraction": 0.85,
        "alert_level": 0.8,
        "sessions_in_window": 18,
        "window_start": "2026-08-01T00:00:00+00:00",
        "period_key": "2026-08-01",
        "reset_at": "2026-09-01T00:00:00+00:00",
        "breakdown_by_agent": {
          "claude": {"cost": 42.5, "tokens": 540000}
        }
      }
    ]
  }
  ```

#### `PUT /budgets`
- **Location**: [`main.py:L9834-L9844`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9834-L9844)
- **Description**: Replaces the full budget list in `~/.tokentelemetry/budgets.json`.
- **Request Body**: `{"budgets": [ ... ]}` or a bare array `[ ... ]`
- **Response Model**: `200 OK`
  ```json
  {
    "ok": true,
    "budgets": [ ... ]
  }
  ```

#### `GET /notifications`
- **Location**: [`main.py:L9810-L9817`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9810-L9817)
- **Description**: Returns all live (non-cleared) notifications, unread counts, and items to toast.
- **Response Model**: `200 OK`
  ```json
  {
    "notifications": [
      {
        "id": 1,
        "kind": "budget_alert",
        "dedup_key": "budget:uuid:2026-08-01:0.8",
        "severity": "warn | over | info",
        "title": "Budget alert: Claude · my-app",
        "body": "$42.50 / $50 (85%)",
        "href": "/projects/my-app/insights",
        "created_at": "2026-08-21T10:00:00+00:00",
        "toasted": true,
        "read": false,
        "cleared": false
      }
    ],
    "unread_count": 1,
    "to_toast": []
  }
  ```

#### `POST /notifications/toasted`
- **Location**: [`main.py:L9819-L9822`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9819-L9822)
- **Description**: Marks notifications as toasted so they are not presented again in banners.
- **Request Body** (optional): `{"ids": [1, 2]}` or empty body `{}` (marks all).
- **Response Model**: `200 OK` `{"ok": true, "updated": 2}`

#### `POST /notifications/read`
- **Location**: [`main.py:L9824-L9827`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9824-L9827)
- **Description**: Marks notifications as read.
- **Request Body** (optional): `{"ids": [1, 2]}` or empty body `{}` (marks all).
- **Response Model**: `200 OK` `{"ok": true, "updated": 2}`

#### `POST /notifications/clear`
- **Location**: [`main.py:L9829-L9832`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9829-L9832)
- **Description**: Marks notifications as cleared (hidden from notification list).
- **Request Body** (optional): `{"ids": [1, 2]}` or empty body `{}` (clears all).
- **Response Model**: `200 OK` `{"ok": true, "updated": 2}`

---

### 3.5 Configuration, Settings, & Hardware Modeling

#### `GET /config`
- **Location**: [`main.py:L10634-L10780`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L10634-L10780)
- **Description**: Discovers and returns skills, MCP servers, memory files (`CLAUDE.md`, `AGENTS.md`), slash commands, custom subagents, and plugins across user and optional project scopes.
- **Query Parameters**:
  - `project` (str, optional): Project path. Validated against `_project_within_safe_roots`.
- **Response Model**: `200 OK`
  ```json
  {
    "project": "/path/to/project",
    "project_valid": true,
    "skills": [
      {
        "name": "research",
        "description": "...",
        "scope": "user | project",
        "agent": "claude",
        "source": "/path/to/SKILL.md",
        "pluginRef": "plugin-name@marketplace"
      }
    ],
    "mcps": [],
    "memory": [],
    "commands": [],
    "subagents": [],
    "plugins": [],
    "counts": {
      "skills": 5,
      "mcps": 2,
      "memory_files": 2,
      "commands": 4,
      "subagents": 1,
      "plugins": 3
    }
  }
  ```

#### `GET /config/hidden`
- **Location**: [`main.py:L9109-L9111`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9109-L9111)
- **Response Model**: `200 OK` `["/hidden/project/path"]`

#### `POST /config/hide` and `POST /config/unhide`
- **Location**: [`main.py:L9114-L9130`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9114-L9130)
- **Request Body**: `{"path": "/project/path"}`
- **Response Model**: `200 OK` `{"ok": true, "hidden": ["/hidden/path"]}`

#### `GET /config/aliases` and `POST /config/aliases`
- **Location**: [`main.py:L9597-L9613`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9597-L9613)
- **POST Request Body**: `{"/old/path": "/new/canonical/path"}`
- **Response Model**: `200 OK` `{"ok": true, "aliases": { ... }}`

#### `GET /config/update-check` and `POST /config/update-check`
- **Location**: [`main.py:L9132-L9154`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9132-L9154)
- **POST Request Body**: `{"enabled": true}`
- **Response Model**: `200 OK`
  ```json
  {
    "enabled": true,
    "env_forced_off": false,
    "effective": true
  }
  ```

#### `GET /config/telemetry` and `POST /config/telemetry`
- **Location**: [`main.py:L9165-L9197`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9165-L9197)
- **POST Request Body**: `{"enabled": true}`
- **Response Model**: `200 OK`
  ```json
  {
    "enabled": true,
    "env_forced_off": false,
    "is_ci": false,
    "effective": true,
    "notice_ack": true
  }
  ```

#### `POST /config/telemetry/ack`
- **Location**: [`main.py:L9199-L9204`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9199-L9204)
- **Response Model**: `200 OK` `{"notice_ack": true}`

#### `GET /config/telemetry/preview`
- **Location**: [`main.py:L9206-L9211`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9206-L9211)
- **Description**: Returns preview of telemetry payload, sample events, recently transmitted events, and privacy guarantees.
- **Response Model**: `200 OK` (Full schema defined in [`telemetry.py:L359-L376`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/telemetry.py#L359-L376)).

#### `POST /telemetry/event`
- **Location**: [`main.py:L9213-L9224`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9213-L9224)
- **Description**: Bridge endpoint for frontend client events (`page.viewed`, `analytics.filtered`, `feature.used`).
- **Request Body**: `{"event": "page.viewed", "props": {"route": "analytics"}}`
- **Response Model**: `200 OK` `{"ok": true}`

#### `GET /config/retention`
- **Location**: [`main.py:L9246-L9262`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9246-L9262)
- **Description**: Per-agent transcript retention windows, archive opt-in flags, and SQLite storage stats.
- **Response Model**: `200 OK`
  ```json
  {
    "agents": {
      "claude": {
        "label": "Claude Code",
        "default_days": 30,
        "effective_days": 30,
        "detected_override": null,
        "configurable": true,
        "settings_hint": "~/.claude/settings.json → cleanupPeriodDays",
        "note": "Purges transcripts older than the window on every startup.",
        "archivable": true,
        "archive_enabled": false
      }
    },
    "storage": {
      "sessions_rows": 120,
      "transcripts_rows": 0,
      "summaries_rows": 15,
      "db_bytes": 65536,
      "transcript_bytes": 0
    },
    "coverage": {}
  }
  ```

#### `POST /config/retention`
- **Location**: [`main.py:L9264-L9278`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9264-L9278)
- **Request Body**: `{"agent": "claude", "enabled": true}`
- **Response Model**: `200 OK` `{"ok": true, "archive": {"claude": true}}`

#### `DELETE /history/transcripts`
- **Location**: [`main.py:L9280-L9289`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9280-L9289)
- **Query Parameters**:
  - `agent` (str, optional): Filter by agent.
  - `older_than_days` (int, optional): Filter by age threshold.
- **Response Model**: `200 OK` `{"ok": true, "deleted": 5, "storage": { ... }}`

#### `GET /config/power` and `PUT /config/power`
- **Location**: [`main.py:L9291-L9325`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9291-L9325)
- **GET Response Model**:
  ```json
  {
    "loadWatts": 80,
    "costPerKwh": 0.15,
    "gridCarbonIntensity": 400,
    "subscriptionEndpoints": [],
    "subscriptionModels": [],
    "localEndpoints": [],
    "referenceCloudModel": "claude-sonnet-4-6",
    "configured": true,
    "deviceDefault": {"watts": 80, "source": "apple-silicon-default"}
  }
  ```
- **PUT Request Body**: `{"loadWatts": 90, "costPerKwh": 0.18, ...}`
- **PUT Response Model**: Full updated config dictionary with `"configured": true`.

#### `GET /config/power/meter`
- **Location**: [`main.py:L9327-L9337`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9327-L9337)
- **Description**: Real-time non-root hardware power reading (via `nvidia-smi` or macOS battery `ioreg`).
- **Response Model**: `200 OK`
  ```json
  {
    "capability": {"available": true, "source": "macos-battery | nvidia-smi", "reason": null},
    "reading": 18.5
  }
  ```

#### `POST /config/power/calibrate`
- **Location**: [`main.py:L9339-L9364`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9339-L9364)
- **Description**: Samples power draw for 4 seconds or falls back to chip-aware baseline estimate.
- **Response Model**: `200 OK`
  ```json
  {
    "measured": 22.4,
    "source": "macos-battery",
    "samples": [21.8, 23.0, 22.4]
  }
  ```

#### `GET /config/billing` and `PUT /config/billing`
- **Location**: [`main.py:L9366-L9405`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9366-L9405)
- **GET Response Model**:
  ```json
  {
    "agents": {
      "claude": {
        "mode": "subscription",
        "source": "user | detected | default",
        "detected": "subscription",
        "default": "subscription",
        "detect_source": "ANTHROPIC_API_KEY env var"
      }
    },
    "modes": ["subscription", "api", "local", "unknown"]
  }
  ```
- **PUT Request Body**: `{"agent": "claude", "mode": "api" | null}`
- **PUT Response Model**: Same as GET.

#### `GET /config/billing-route` and `PUT /config/billing-route`
- **Location**: [`main.py:L9526-L9595`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9526-L9595)
- **Description**: Drain-priority billing routes split by task type (`interactive` vs `programmatic`), managing credit pool sizes and overflow rules.
- **GET Response Model**:
  ```json
  {
    "agents": {
      "claude": {
        "buckets": [
          {
            "id": "sdk_credit",
            "label": "Agent SDK credit",
            "charges": "included",
            "task_types": ["programmatic"],
            "pool_usd": 20.0,
            "pool_requests": null,
            "pool_period": "month",
            "no_spillover": true,
            "note": "..."
          }
        ],
        "routes": {
          "interactive": {"bucket": "subscription", "charges": "included", "warn_at": null},
          "programmatic": {"bucket": "sdk_credit", "charges": "included", "warn_at": 20.0}
        },
        "plan": "pro"
      }
    },
    "task_types": ["interactive", "programmatic"],
    "charges": ["included", "api_rate", "electricity"],
    "as_of": "2026-06-11"
  }
  ```
- **PUT Request Body**: `{"agent": "claude", "plan": "max5x" | null}`
- **PUT Response Model**: Same as GET.

#### `GET /config/agent-features`
- **Location**: [`main.py:L9510-L9524`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9510-L9524)
- **Description**: Surfaces scalar/boolean feature flags from local agent configs (Copilot, Codex, Claude Code).
- **Response Model**: `200 OK`
  ```json
  {
    "agents": [
      {
        "agent": "copilot",
        "detected": true,
        "source": "~/.copilot/settings.json",
        "flags": [{"name": "experimental", "value": true, "kind": "bool"}],
        "note": "...",
        "how_to_enable": "/experimental",
        "enable_command": "/experimental",
        "docs_url": "https://..."
      }
    ],
    "not_detectable": [
      {
        "agent": "antigravity",
        "reason": "Its Scheduled Tasks and preview features live in an opaque local state store (state.vscdb) / server-side, not a readable flag."
      }
    ]
  }
  ```

---

### 3.6 Trace Summarization Endpoints

#### `GET /summarizer/available`
- **Location**: [`main.py:L10800-L10804`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L10800-L10804)
- **Response Model**: `200 OK`
  ```json
  {
    "backends": [
      {"name": "ollama", "display_name": "Ollama (Local)"},
      {"name": "claude", "display_name": "Claude CLI"},
      {"name": "openai_compat", "display_name": "OpenAI Compatible"}
    ]
  }
  ```

#### `GET /config/summarizer` and `PUT /config/summarizer`
- **Location**: [`main.py:L10806-L10830`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L10806-L10830)
- **PUT Request Body**:
  ```json
  {
    "enabled": true,
    "backend": "ollama",
    "model": "llama3.2:latest",
    "openai_compat": {
      "endpoint": "http://localhost:8080/v1",
      "api_key": null,
      "temperature": 0.2
    }
  }
  ```
- **Response Model**: `200 OK` (Saved config dictionary).

#### `GET /summarizer/ollama/models` & `GET /summarizer/codex/models`
- **Location**: [`main.py:L10832-L10847`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L10832-L10847)
- **Response Model**: `200 OK` `{"models": ["llama3.2:latest", "mistral:latest"]}`

#### `POST /summarizer/openai-compat/test`
- **Location**: [`main.py:L10849-L10869`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L10849-L10869)
- **Request Body**: `{"model": "...", "openai_compat": { ... }}`
- **Response Model**: `200 OK`
  ```json
  {
    "ok": true,
    "sample": "ok",
    "endpoint": "http://localhost:8080/v1"
  }
  ```

#### `GET /sessions/{session_id}/summary`
- **Location**: [`main.py:L10871-L10874`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L10871-L10874)
- **Response Model**: `200 OK` `{"summary": { ... } | null}`

#### `POST /sessions/{session_id}/summary`
- **Location**: [`main.py:L10876-L10928`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L10876-L10928)
- **Query Parameters**: `agent` (str, required), `force` (bool, default `False`)
- **Response Model**: `200 OK`
  ```json
  {
    "summary": {
      "session_id": "sid",
      "agent": "claude",
      "content_hash": "sha256...",
      "backend": "ollama",
      "model": "llama3.2",
      "brief": {
        "intent": "Fix bug in API router",
        "actions": ["edited main.py", "ran tests"],
        "errors": [],
        "cost": 0.02
      },
      "narrative": {
        "summary": "Resolved bug in router by adding missing route decorator.",
        "key_decisions": [],
        "outcome": "success"
      },
      "summary_cost": 0.0,
      "generated_at": "2026-08-21T10:00:00Z",
      "stale": false
    },
    "error": null,
    "error_info": null
  }
  ```

#### `POST /summaries/recent`
- **Location**: [`main.py:L10929-L10946`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L10929-L10946)
- **Query Parameters**: `limit` (int, default `20`)
- **Response Model**: `200 OK`
  ```json
  {
    "requested": 20,
    "summarized": 15,
    "skipped": 5,
    "failed": 0
  }
  ```

---

### 3.7 Hermes Autonomous Agent Subsystem

#### `GET /hermes/overview`
- **Location**: [`main.py:L2427-L2437`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L2427-L2437)
- **Response Model**: `200 OK`
  ```json
  {
    "installed": true,
    "gateway": {"running": true, "pid": 12345, "port": 8080},
    "cron_jobs": []
  }
  ```

#### `GET /hermes/telemetry`
- **Location**: [`main.py:L2439-L2454`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L2439-L2454)
- **Description**: Computes outcome classifications, cost breakdowns with confidence levels, API latency percentiles (p50, p95), and tool failure rates from `agent.log*`.
- **Response Model**: `200 OK` (Built by [`hermes_telemetry.py:L571-L590`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/hermes_telemetry.py#L571-L590)).

#### `GET /hermes/sessions`
- **Location**: [`main.py:L2537-L2599`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L2537-L2599)
- **Query Parameters**:
  - `page` (int, default `1`)
  - `page_size` (int, default `50`, max `200`)
  - `search` (str, optional)
  - `project` (str, optional)
  - `source` (str, optional)
  - `model` (str, optional)
  - `sort` (str, default `"newest"`)
  - `fresh` (bool, default `False`)
- **Response Model**: `200 OK`
  ```json
  {
    "sessions": [ ... ],
    "pagination": {
      "page": 1,
      "page_size": 50,
      "total": 120,
      "total_pages": 3
    }
  }
  ```

#### `GET /hermes/skills`
- **Location**: [`main.py:L1529-L1563`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L1529-L1563)
- **Response Model**: `200 OK` `{"snapshot_loaded": 12, "skills": [ ... ], "categories": { ... }}`

#### `GET /hermes/memory`
- **Location**: [`main.py:L1577-L1587`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L1577-L1587)
- **Response Model**: `200 OK` `{"memory": {"entries": [], "char_count": 0, "exists": true}, "user": { ... }, "memory_char_limit": 2200, "user_char_limit": 1375}`

#### `GET /hermes/soul`
- **Location**: [`main.py:L1589-L1600`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L1589-L1600)
- **Response Model**: `200 OK` `{"content": "...", "exists": true}`

#### `GET /hermes/profiles`
- **Location**: [`main.py:L1631-L1732`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L1631-L1732)
- **Response Model**: `200 OK` `{"profiles": [ ... ], "active_profile": "default"}`

#### `GET /hermes/kanban`
- **Location**: [`main.py:L1768-L1875`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L1768-L1875)
- **Response Model**: `200 OK` `{"installed": true, "boards": [ ... ]}`

#### `GET /hermes/tools`
- **Location**: [`main.py:L1877-L1894`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L1877-L1894)
- **Response Model**: `200 OK` `{"enabled_tools": ["cli", "filesystem"]}`

---

### 3.8 DeepSeek Harness (DSH) & Cache Management

#### `GET /dsh/lifecycle`
- **Location**: [`main.py:L4549-L4575`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L4549-L4575)
- **Query Parameters**:
  - `session_id` (str, optional)
  - `limit` (int, default `500`)
- **Response Model**: `200 OK`
  ```json
  {
    "installed": true,
    "correlation": "none | time-window",
    "events": [ ... ]
  }
  ```

#### `GET /cache/status`
- **Location**: [`main.py:L7558-L7569`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L7558-L7569)
- **Response Model**: `200 OK`
  ```json
  {
    "cached": true,
    "age_sec": 4.25,
    "ttl_sec": 30.0,
    "entries": 150,
    "building": false,
    "last_error": null
  }
  ```

#### `POST /cache/invalidate`
- **Location**: [`main.py:L7571-L7577`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L7571-L7577)
- **Response Model**: `200 OK` `{"ok": true}`

---

## 4. Real-Time Event Streaming & WebSocket Analysis

### 4.1 Absence of SSE and WebSocket Protocols
An exhaustive audit across both `repositories/tokentelemetry/backend/` and `repositories/tokentelemetry/frontend/` reveals that **no WebSocket (`ws://` / `wss://`) or Server-Sent Events (`text/event-stream`) endpoints exist**:
1. All client-to-server and dashboard communications operate over standard HTTP 1.1 / HTTP 2 REST calls.
2. Dashboard live data updates rely exclusively on HTTP client-side polling (`useResource` in `frontend/src/lib/api.ts` executing periodic `GET` requests).
3. Backend log ingestion relies on file-system watches, mtime checks, and SQLite transactions triggered during request processing or worker scans.

### 4.2 Event Protocols & Push Architecture

| Subsystem | Transport / Mechanism | Payload / Schema Format | Destination / Persistence |
| :--- | :--- | :--- | :--- |
| **Product Telemetry** | HTTP POST (Fire-and-forget daemon thread) | JSON (`app.launched`, `page.viewed`, `trace.summarized`, `analytics.filtered`, `feature.used`) | Cloudflare Worker (`https://tt-telemetry-proxy.tokentelemetry.workers.dev`) |
| **Notification Center** | SQLite write + HTTP polling | JSON (`id`, `kind`, `dedup_key`, `severity`, `title`, `body`, `href`, `toasted`, `read`, `cleared`) | Local `~/.tokentelemetry/notifications.db` |
| **DSH Lifecycle** | JSONL append via sidecar plugin | JSONL (`event`, `plugin`, `state`, `ts`) | `~/.tokentelemetry/dsh_lifecycle.jsonl` |
| **Grok Build Events** | Append-only JSONL files on disk | JSONL (`events.jsonl`, `updates.jsonl`, `chat_history.jsonl`) | `~/.grok/sessions/<project>/<uuid>/` |
| **Hermes Gateway Logs**| Rotated log files (`agent.log`, `agent.log.1`, `agent.log.2`) | Structured log lines (parsed via regex into API calls, latency, tool calls) | `~/.hermes/logs/` |

---

## 5. Architectural Recommendations for Go Rewrite

1. **Routing & Middleware**:
   - Implement handlers matching the exact URL paths and HTTP methods mapped above using Go's standard library `net/http` (Go 1.22+ routing) or a lightweight router like `chi`.
   - Port `RemoteAuthMiddleware` to check loopback IP addresses, extract Bearer or `?token=` parameters, and perform constant-time authentication checks with `crypto/subtle.ConstantTimeCompare`.
2. **Data Stores & Concurrency**:
   - Utilize `modernc.org/sqlite` (pure Go SQLite) or `mattn/go-sqlite3` (CGO) in WAL mode with connection pools for `history.db`, `notifications.db`, and `summaries.db`.
3. **Optional Real-Time Enhancement**:
   - The Go implementation can introduce an optional SSE (`/events`) or WebSocket stream for instant updates to the frontend while remaining 100% backward compatible with the polling `GET /sessions`, `GET /analytics`, and `GET /notifications` endpoints.
