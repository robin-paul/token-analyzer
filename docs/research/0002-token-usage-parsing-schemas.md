# Reverse-Engineered Token Usage Extraction & Parsing Schemas Across Agent Ecosystems

**Ticket:** Wayfinder Research #2 (Part of Map #1: TokenTelemetry Go Port Architecture)  
**Target Repository:** `repositories/tokentelemetry/backend/`  
**Primary Source References:**
- Architecture & Principles: [`DESIGN.md`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/DESIGN.md#L1-L194)
- Core Scanner & Extractors: [`main.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L1-L11008)
- Pricing & Cost Computation: [`pricing.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L1-L409)
- Hermes Telemetry & Outcomes: [`hermes_telemetry.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/hermes_telemetry.py#L1-L590)
- Summarization & Condensation: [`summaries.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/summaries.py#L1-L424)
- Test Suites & Verified Fixtures: [`test_delegation.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/test_delegation.py), [`test_antigravity_cli.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/test_antigravity_cli.py), [`test_copilot_cli_metrics.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/test_copilot_cli_metrics.py), [`test_cline_smallcode.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/test_cline_smallcode.py), [`test_dsh_scan.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/test_dsh_scan.py), [`test_pi_scan.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/test_pi_scan.py)

---

## Executive Summary & Core Architectural Invariants

The `tokentelemetry` ingestion engine parses telemetry across diverse agent ecosystems into a unified data contract. The port to a single Go binary requires reproducing the following critical invariants:

1. **The Count-Once Invariant ([`DESIGN.md:94-109`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/DESIGN.md#L94-L109)):**
   - Every token is counted in project/ecosystem aggregates exactly once.
   - **Internal File Spawns (Claude Code, DSH, Muse):** Subagent runs are contained in files/directories under the parent session. Because they are NOT top-level sessions, their usage is rolled into a dedicated `delegation` / `delegated_*` bucket on the parent and added to global totals.
   - **Sibling / Database Sessions (OpenCode, Hermes, Codex, Grok Build, Antigravity CLI, Cline):** Spawned child agents exist as standalone session rows or directories. Their tokens are already counted in primary aggregates as independent sessions. Therefore, parent records only maintain linkage annotations (`parent_session_id`, `child_session_ids`, `linked_children`), and delegated sums are strictly display-only to prevent double-billing.

2. **Zero-Trust & Honest "n/a" ([`DESIGN.md:3-6`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/DESIGN.md#L3-L6), [`main.py:4783-4785`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L4783-L4785)):**
   - Only agents in `_DELEGATION_CAPABLE_AGENTS = {"claude", "cursor", "opencode", "hermes", "grok", "codex", "antigravity", "cline"}` report `delegation.supported = true`.
   - All other agents report `{"supported": false}` (rendered as "not recorded by <agent>", never a fake 0).
   - If an agent logs spawns but no token data (e.g. Cursor), `tokens_recorded = false` and token counts remain `null` / unrecorded.

3. **Cache Token Semantics ([`pricing.py:285-409`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L285-L409), [`main.py:5056-5108`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L5056-L5108)):**
   - **Cache Read:** `cached` in UI displays the high-water mark (maximum) of cache reads per transcript, but pricing is calculated on cumulative cache read tokens (`_cached_sum`).
   - **Cache Write (Creation):** `cache_creation` tokens are cumulative per turn and billed at **1.25x** the base prompt input rate for standard 5-minute TTL, or **2.0x** for 1-hour ephemeral TTL (`cache_creation_1h`).

4. **Net vs. Gross Prompt Input ([`main.py:78-127`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L78-L127), [`main.py:6201-6227`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L6201-L6227)):**
   - Certain APIs/logs (OpenAI, Codex, Copilot CLI) report `inputTokens` as GROSS (including cache read and cache write tokens). The parser nets out cached tokens: `net_input = max(0, gross_input - cache_read - cache_write)`.

---

## Ecosystem-by-Ecosystem Extraction & Parsing Specifications

```
+-------------------------------------------------------------------------------------------------------------------------------+
| AI Agent Ecosystem       | Storage Type   | File Path / Pattern                          | Token Fields Available             |
+--------------------------+----------------+----------------------------------------------+------------------------------------+
| 1. Claude Code           | JSONL          | ~/.claude/projects/<p>/<sid>.jsonl           | in, out, cache_read, cache_create  |
| 2. Cursor                | JSONL          | ~/.cursor/projects/<p>/agent-transcripts/    | in, out, cache_read, cache_create  |
| 3. OpenCode              | SQLite         | ~/.local/share/opencode/opencode*.db         | in, out, cache_read, cache_write   |
| 4. Hermes                | SQLite + Logs  | ~/.hermes/state.db, profiles/*/state.db      | in, out, cache_read/write, reason  |
| 5. Grok Build            | JSON + JSONL   | ~/.grok/sessions/<p>/<sid>/                  | contextTokensUsed (gross in)       |
| 6. Codex                 | JSONL          | ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl | in (gross), cached_in, out, reason |
| 7. Antigravity CLI (agy) | SQLite + JSONL | ~/.gemini/antigravity-cli/                   | trajectory heuristics + token cache|
| 8. GitHub Copilot        | JSON + JSONL   | VS Code storage & ~/.copilot/session-state/  | in (gross/est), out, cache r/w     |
| 9. Cline & SmallCode     | SQLite & JSON  | ~/.cline/data/db/ & <proj>/.smallcode/       | in, out, cacheRead, cacheWrite     |
| 10. Pi Coding Agent      | JSONL          | ~/.pi/agent/sessions/<p>/<sid>.jsonl         | in, out, cacheRead, cacheWrite     |
| 11. DeepSeek Harness     | JSONL (zstd)   | ~/.dsh/sessions/<p>/<sid>/session.jsonl.zstd | in, out (deduped across chunks)    |
| 12. Meta Muse & Prime    | JSONL          | ~/.muse/ & ~/.prime/                         | in, out, cache_read/write, reason  |
| 13. Qwen & Vibe          | JSONL & JSON   | ~/.qwen/projects/ & ~/.vibe/logs/            | in, out, cached                    |
+-------------------------------------------------------------------------------------------------------------------------------+
```

---

### 1. Claude Code

- **Root Directories:** [`main.py:277`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L277)
  - `~/.claude/projects/<encoded-cwd>/<sessionId>.jsonl`
  - Legacy metadata: `~/.claude/history.jsonl`
  - Memory artifacts: `~/.claude/projects/<encoded-cwd>/memory/*.md`
- **Subagent Transcripts & Workflows:** [`main.py:5122-5250`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L5122-L5250)
  - Task/Agent tool subagents: `~/.claude/projects/<encoded-cwd>/<sessionId>/subagents/agent-<agentId>.jsonl` and metadata sidecar `agent-<agentId>.meta.json`
  - Dynamic workflow subagents: `~/.claude/projects/<encoded-cwd>/<sessionId>/subagents/workflows/wf_<workflowId>/agent-<agentId>.jsonl` with mapping in `journal.jsonl`
- **JSONL Schema:**
  - `meta.json`: `{"agentType": "Explore", "description": "...", "toolUseId": "toolu_..."}`
  - `journal.jsonl`: `{"type": "result", "agentId": "wfa", "result": {"area": "Phase A", "summary": "..."}}`
  - Assistant turn JSONL line:
    ```json
    {
      "type": "assistant",
      "sessionId": "11111111-2222-3333-4444-555555555555",
      "isSidechain": true,
      "agentId": "agent-one",
      "attributionAgent": "Explore",
      "message": {
        "id": "msg_12345",
        "model": "claude-haiku-4-5-20251001",
        "usage": {
          "input_tokens": 100,
          "output_tokens": 50,
          "cache_read_input_tokens": 1000,
          "cache_creation_input_tokens": 200,
          "cache_creation": {
            "ephemeral_1h_input_tokens": 0
          }
        },
        "content": [
          {"type": "tool_use", "id": "toolu_1", "name": "Skill", "input": {"skill": "review"}}
        ]
      }
    }
    ```
- **Extraction & Delegation Logic ([`main.py:5048-5250`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L5048-L5250), [`main.py:6057-6071`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L6057-L6071)):**
  - Model pricing is calculated **per subagent file** using that file's specific model (e.g. Haiku vs. parent Opus).
  - Parent session receives `tokens.delegated_input`, `tokens.delegated_output`, `tokens.delegated_cached`, `tokens.delegated_cache_creation`, `delegated_cost`, and `delegation: {supported: true, tokens_recorded: true, spawn_count, by_type}`.
  - Skills and MCPs: Extracted from `content` tool calls `name: "Skill"` (`input.skill`), slash command tags `<command-name>/<cmd></command-name>` in user messages, and `mcp__<server>__<tool>` patterns.
  - Loops: Detected via tool calls `CronCreate` (fixed cron), `ScheduleWakeup` (dynamic delay), `CronDelete` / `CronStop`.
  - Hosted Artifacts: Regex `https://claude.ai/code/artifact/[0-9a-f-]{36}` in `Artifact` tool results.

---

### 2. Cursor

- **Root Directories:** [`main.py:282`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L282), [`main.py:6695-6801`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L6695-L6801)
  - Transcripts: `~/.cursor/projects/<project-slug>/agent-transcripts/<sessionId>/<sessionId>.jsonl`
  - Subagents: `~/.cursor/projects/<project-slug>/agent-transcripts/<sessionId>/subagents/<uuid>.jsonl`
  - Workspace map: `<VSCode/Cursor Global Storage>/*/workspace.json`
  - Terminal logs: `~/.cursor/projects/<project-slug>/terminals/*.txt`
- **JSONL Schema:**
  - Assistant turn:
    ```json
    {
      "role": "assistant",
      "message": {
        "model": "claude-3-5-sonnet",
        "usage": {
          "input_tokens": 1200,
          "output_tokens": 300,
          "cache_read_input_tokens": 4000,
          "cache_creation_input_tokens": 500
        },
        "content": [
          {"type": "tool_use", "name": "Subagent", "input": {"name": "frontend-dev"}}
        ]
      }
    }
    ```
- **Extraction & Delegation Logic:**
  - Main transcript has standard token usage fields (`input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`).
  - **Subagent files contain NO usage or model metrics** (plain `{role, message}`).
  - Scanner records `delegation: {supported: true, tokens_recorded: false, spawn_count: max(subagents_dir_count, subagent_tool_calls)}`. No tokens or costs are fabricated.

---

### 3. OpenCode

- **Root Directories:** [`main.py:330-408`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L330-L408), [`main.py:6929-7107`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L6929-L7107)
  - Data paths: `$OPENCODE_DATA_DIR`, `$XDG_DATA_HOME/opencode/`, `~/.local/share/opencode/`, `~/Library/Application Support/opencode/`
  - SQLite files: `opencode*.db` (e.g. `opencode.db`, `opencode-stable.db`, `opencode-beta.db`)
- **SQLite Tables & Schemas:**
  - Table `session`: `id TEXT PRIMARY KEY, directory TEXT, title TEXT, time_created INTEGER, time_updated INTEGER, model TEXT, parent_id TEXT`
  - Table `message`: `id TEXT, session_id TEXT, time_created INTEGER, data TEXT (JSON)`
    - `data`: `{"role": "assistant", "providerID": "anthropic", "modelID": "claude-sonnet-4-6", "mode": "plan"}`
  - Table `part`: `id TEXT, session_id TEXT, message_id TEXT, time_created INTEGER, data TEXT (JSON)`
    - Step-finish JSON:
      ```json
      {
        "type": "step-finish",
        "tokens": {
          "input": 1500,
          "output": 250,
          "cache": {
            "read": 5000,
            "write": 600
          }
        }
      }
      ```
    - Tool call JSON: `{"type": "tool", "tool": "read_file"}`
    - User text JSON: `{"type": "text", "text": "<system-reminder>...</system-reminder>Actual prompt"}`
  - Table `todo`: `session_id TEXT, content TEXT, status TEXT, position INTEGER`
- **Extraction & Delegation Logic:**
  - Tokens: Summed from `part` rows where `type == 'step-finish'`. Cache reads take the maximum; cache writes accumulate and are priced at 1.25x.
  - Hierarchy: `session.parent_id` links child to parent. Children are already standalone sessions in the SQLite DB; parent is annotated with `child_session_ids` and `delegation: {supported: true, tokens_recorded: false, linked_children: N}`.

---

### 4. Hermes

- **Root Directories:** [`main.py:430-432`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L430-L432), [`main.py:7137-7334`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L7137-L7334)
  - Main DB: `~/.hermes/state.db` (or `$HERMES_HOME/state.db`)
  - Profile DBs: `~/.hermes/profiles/*/state.db`
  - Logs: `~/.hermes/logs/agent.log*` (parsed via [`hermes_telemetry.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/hermes_telemetry.py))
  - Skills & Memories: `~/.hermes/.skills_prompt_snapshot.json`, `~/.hermes/memories/`, `~/.hermes/SOUL.md`
- **SQLite Schema (`sessions` & `messages` tables):**
  - Table `sessions`:
    ```sql
    CREATE TABLE sessions (
      id TEXT PRIMARY KEY,
      source TEXT,
      model TEXT,
      parent_session_id TEXT,
      started_at INTEGER,
      ended_at INTEGER,
      input_tokens INTEGER,
      output_tokens INTEGER,
      cache_read_tokens INTEGER,
      cache_write_tokens INTEGER,
      reasoning_tokens INTEGER,
      estimated_cost_usd REAL,
      actual_cost_usd REAL,
      title TEXT,
      billing_provider TEXT,
      billing_base_url TEXT,
      cost_status TEXT,
      cost_source TEXT,
      end_reason TEXT
    );
    ```
- **Extraction & Delegation Logic:**
  - Token Breakdown: `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `reasoning_tokens`.
  - Reasoning Anomaly: Flagged when `reasoning_tokens > 5000 and reasoning_tokens > output_tokens`.
  - Cost Prioritization: `actual_cost_usd` (provider-reported) > `estimated_cost_usd` (provider-estimated) > TokenTelemetry `calculate_cost(...)` (tt-computed / zero-marginal).
  - Outcome Classification: `end_reason` mapped via [`hermes_telemetry.py:OUTCOME_BUCKETS`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/hermes_telemetry.py#L42-L80) into: `completed`, `interrupted`, `timed_out`, `continued`, `reset`, `errored`, `unknown`.
  - Hierarchy: `parent_session_id` links child to parent. Children are already sessions in SQLite; parent receives `child_session_ids` and `delegation: {supported: true, tokens_recorded: false, linked_children: N}`.

---

### 5. Grok Build (xAI)

- **Root Directories:** [`main.py:436-437`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L436-L437), [`main.py:3082-3330`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L3082-L3330)
  - `~/.grok/sessions/<url-encoded-cwd>/<sessionId>/`
- **File Structure & Schemas:**
  - `summary.json`:
    ```json
    {
      "created_at": "2026-06-10T07:00:00Z",
      "updated_at": "2026-06-10T07:01:00Z",
      "generated_title": "Grok Session Title",
      "session_summary": "Summary text...",
      "current_model_id": "grok-build",
      "info": {"cwd": "/path/to/project"},
      "num_messages": 12,
      "agent_name": "build-agent"
    }
    ```
  - `signals.json`:
    ```json
    {
      "contextTokensUsed": 45200,
      "toolsUsed": ["read_file", "edit_file", "spawn_subagent"],
      "modelsUsed": ["grok-build"]
    }
    ```
  - `subagents/<childSessionId>/meta.json`:
    ```json
    {
      "subagent_id": "019eb056-646a-7a03-b3f7-000000000002",
      "parent_session_id": "019eb056-455f-7442-bf79-000000000001",
      "child_session_id": "019eb056-646a-7a03-b3f7-000000000002",
      "subagent_type": "general-purpose",
      "description": "Summarize README",
      "status": "completed",
      "duration_ms": 5898,
      "tool_calls": 1,
      "turns": 1,
      "effective_model_id": "grok-build"
    }
    ```
  - `plan_mode.json`: `{"state": "Active", "was_previously_active": true}`
- **Extraction & Delegation Logic:**
  - Token Breakdown: Grok records no prompt/completion split; `signals.contextTokensUsed` represents the measured context footprint and is mapped to `input = contextTokensUsed`, `output = 0`, `cached = 0`. Fallback scans `updates.jsonl` for max `params._meta.totalTokens`.
  - Hierarchy: Parent session scans `subagents/*/meta.json`. Child is a full sibling directory in the same project bucket. Parent gets `child_session_ids` and `delegation: {supported: true, tokens_recorded: false, spawn_count, by_type: {...}}`.

---

### 6. Codex

- **Root Directories:** [`main.py:278`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L278), [`main.py:6076-6310`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L6076-L6310)
  - `~/.codex/sessions/YYYY/MM/DD/rollout-<timestamp>-<sessionId>.jsonl`
  - Legacy thread index: `~/.codex/session_index.jsonl` (frozen in recent versions; discovery is performed directly on rollout files)
- **JSONL Schema:**
  - `session_meta`:
    ```json
    {
      "timestamp": "2026-06-10T07:01:46.921Z",
      "type": "session_meta",
      "payload": {
        "id": "019eb056-83a6-7fe0-99ce-000000000002",
        "cwd": "/path/to/project",
        "model_provider": "openai",
        "cli_version": "0.136.0",
        "thread_source": "subagent",
        "forked_from_id": "019eb056-4eae-7280-8617-000000000001",
        "source": {
          "subagent": {
            "thread_spawn": {
              "parent_thread_id": "019eb056-4eae-7280-8617-000000000001",
              "depth": 1,
              "agent_nickname": "Dewey",
              "agent_role": "explorer"
            }
          }
        }
      }
    }
    ```
  - `event_msg` (token count):
    ```json
    {
      "type": "event_msg",
      "payload": {
        "type": "token_count",
        "info": {
          "total_token_usage": {
            "input_tokens": 1500,
            "cached_input_tokens": 1000,
            "output_tokens": 200,
            "reasoning_output_tokens": 50,
            "total_tokens": 1700
          }
        }
      }
    }
    ```
  - `response_item` (function call / skills / plans):
    ```json
    {
      "type": "response_item",
      "payload": {
        "type": "function_call",
        "name": "exec_command",
        "arguments": "{\"cmd\": [\"cat\", \"~/.codex/skills/review/SKILL.md\"]}"
      }
    }
    ```
- **Extraction & Delegation Logic:**
  - Token Netting: `gross_input = input_tokens`, `cached = cached_input_tokens`. `net_input = max(0, gross_input - cached)`. Billable output adds `reasoning_output_tokens` only if `total_tokens > gross_input + output_tokens`.
  - Hierarchy: Subagent rollouts carry `thread_source: "subagent"` and `source.subagent.thread_spawn`. Children are standalone session files; parent is linked via `parent_session_id` and receives `child_session_ids` and `delegation: {supported: true, tokens_recorded: false, linked_children: N}`.
  - Skill Breadcrumbs: Detected from tool call regex matching `.../skills/<skill_name>/SKILL.md`.
  - Goal Mode: Joined dynamically from `codex_goals.py` via thread ID.

---

### 7. Antigravity CLI (`agy`) & Antigravity IDE / App

- **Root Directories:** [`main.py:453-469`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L453-L469), [`main.py:863-991`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L863-L991), [`main.py:1120-1335`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L1120-L1335), [`main.py:6487-6620`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L6487-L6620)
  - Brain roots: `~/.gemini/antigravity-cli/brain/`, `~/.gemini/antigravity-ide/brain/`, `~/.gemini/antigravity/brain/`
  - CLI conversation DBs: `~/.gemini/antigravity-cli/conversations/<sid>.db` (SQLite) or `<sid>.pb` (Protobuf)
  - Prompt history: `~/.gemini/antigravity-cli/history.jsonl`
  - Web / Gemini chat: `~/.gemini/tmp/<slug>/chats/*.json` or `*.jsonl`, `logs.json`
- **Schemas:**
  - Brain `transcript.jsonl` / `transcript_full.jsonl`:
    ```json
    {"step_index": 1, "source": "USER_EXPLICIT", "type": "USER_INPUT", "content": "<USER_REQUEST>Fix bug</USER_REQUEST>"}
    {"step_index": 2, "source": "MODEL", "type": "INVOKE_SUBAGENT", "content": "Created subagents:\n{\n  \"conversationId\": \"d5361c61-c969-4f95-89b8-942bc99a4c24\"\n}"}
    {"step_index": 3, "source": "MODEL", "type": "MODEL_RESPONSE", "content": "Running tool", "tool_calls": [{"name": "read_file", "args": {"path": "main.py"}}]}
    ```
  - CLI SQLite `conversations/<sid>.db`:
    - Table `gen_metadata (idx INTEGER, data BLOB)`: Contains protobuf string encoding model name (matched via regex `_AG_MODEL_DISPLAY_RE`).
    - Table `steps (idx INTEGER, step_payload BLOB)`: Contains JSON tool call arguments (`Cwd`, `SearchPath`, `Query`).
- **Extraction & Delegation Logic:**
  - Token Estimation: Computed from transcript character count `len(line) // 4` (`MODEL` -> output, other -> input) and cached in `tokens_cache.json`. Exact tokens used if `chats/*.json` exists.
  - Hierarchy ([`main.py:4794-4840`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L4794-L4840)): Parent transcript `INVOKE_SUBAGENT` content embeds child `conversationId`. Linked across sessions in `_antigravity_link_subagents(...)`: parent gets `child_session_ids` and `delegation: {supported: true, tokens_recorded: false, linked_children: N}`, child gets `parent_session_id`.

---

### 8. GitHub Copilot (VS Code & Copilot CLI)

- **Root Directories:** [`main.py:452`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L452), [`main.py:6803-6927`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L6803-L6927)
  - VS Code Chat: `<Code Storage>/*/chatSessions/<sessionId>.json` or `.jsonl`
  - Copilot CLI: `~/.copilot/session-state/<sessionId>/events.jsonl`
- **Schemas:**
  - VS Code `chatSessions/<sid>.json`:
    ```json
    {
      "version": 3,
      "creationDate": 1781420401161,
      "requests": [
        {
          "message": {"text": "explain function"},
          "modelId": "copilot/gpt-5-mini",
          "timestamp": 1781420405000,
          "completionTokens": 42,
          "thinking": {"tokens": 10, "text": "plan..."}
        }
      ]
    }
    ```
  - Copilot CLI `events.jsonl`:
    ```json
    {"type": "session.start", "data": {"context": {"cwd": "/path/to/project"}, "startTime": "2026-06-10T07:00:00Z"}}
    {"type": "user.message", "data": {"content": "fix issue"}}
    {"type": "assistant.message", "data": {"model": "claude-haiku-4.5", "outputTokens": 1365}}
    {"type": "session.shutdown", "data": {"modelMetrics": {
      "claude-haiku-4.5": {
        "usage": {
          "inputTokens": 63219,
          "outputTokens": 1365,
          "cacheReadTokens": 34516,
          "cacheWriteTokens": 28676,
          "reasoningTokens": 355
        },
        "tokenDetails": {
          "input": {"tokenCount": 27},
          "cache_read": {"tokenCount": 34516},
          "cache_write": {"tokenCount": 28676},
          "output": {"tokenCount": 1365}
        }
      }
    }}}
    ```
- **Extraction Logic ([`main.py:78-127`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L78-L127)):**
  - Copilot CLI `modelMetrics` reports GROSS `inputTokens` (`net input + cacheReadTokens + cacheWriteTokens`).
  - Extractor computes `input = inputTokens - cacheReadTokens - cacheWriteTokens` (matching `tokenDetails.input`), `output = outputTokens`, `cached = cacheReadTokens`, `cache_creation = cacheWriteTokens`.

---

### 9. Cline & SmallCode

- **Root Directories:** [`main.py:476-478`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L476-L478), [`main.py:3492-3881`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L3492-L3881)
  - Cline CLI: `~/.cline/data/db/sessions.db`, `~/.cline/data/db/cron.db`
  - Cline VS Code: `globalStorage/saoudrizwan.claude-dev/state/taskHistory.json`
  - SmallCode: Project-local `<project>/.smallcode/traces/<traceId>.json`
- **Schemas:**
  - Cline CLI `sessions` SQLite table:
    `session_id, started_at, ended_at, exit_code, status, provider, model, cwd, workspace_root, prompt, metadata_json, messages_path, is_subagent, parent_session_id, agent_id, team_name`
    - `metadata_json`:
      ```json
      {
        "usage": {"inputTokens": 100, "outputTokens": 20, "cacheReadTokens": 0},
        "aggregateUsage": {"inputTokens": 150, "outputTokens": 30, "cacheReadTokens": 0},
        "totalCost": 0.05
      }
      ```
  - SmallCode `<project>/.smallcode/traces/<id>.json`:
    ```json
    {
      "id": "8fadca50",
      "model": "nemotron-3-nano:4b",
      "prompt": "Fix bug in math.py",
      "startedAt": "2026-07-01T05:14:54.084Z",
      "endedAt": "2026-07-01T05:15:34.149Z",
      "tokens": {"prompt": 8331, "completion": 185},
      "steps": [{"type": "tool_call", "name": "read_file", "args": {"path": "math.py"}}]
    }
    ```
- **Extraction & Delegation Logic:**
  - Cline Subagents ([`main.py:3687-3734`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L3687-L3734)): Subagents are separate rows with `is_subagent=1` and `parent_session_id`. Because `aggregateUsage` includes children, parent sessions are billed strictly on their OWN `usage` to prevent double-counting.
  - SmallCode: Scanned across project roots discovered from other sessions plus `TT_SMALLCODE_ROOTS`.

---

### 10. Pi Coding Agent (`pi`)

- **Root Directories:** [`main.py:289-290`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L289-L290), [`main.py:3884-4050`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L3884-L4050)
  - `~/.pi/agent/sessions/<encoded-cwd>/<timestamp>_<uuid>.jsonl`
- **JSONL Schema:**
  - Header: `{"type": "session", "version": 3, "id": "sid_123", "cwd": "/path/to/project", "timestamp": "2026-07-05T07:40:17.539Z"}`
  - Model change: `{"type": "model_change", "provider": "cerebras", "modelId": "zai-glm-4.7"}`
  - Message turn:
    ```json
    {
      "type": "message",
      "timestamp": "2026-07-05T07:41:00.789Z",
      "message": {
        "role": "assistant",
        "provider": "cerebras",
        "model": "zai-glm-4.7",
        "content": [
          {"type": "thinking", "thinking": "Thinking..."},
          {"type": "toolCall", "id": "tc1", "name": "read", "arguments": {"path": "/docs"}}
        ],
        "usage": {
          "input": 2965,
          "output": 185,
          "cacheRead": 100,
          "cacheWrite": 50,
          "reasoning": 100,
          "totalTokens": 3250
        }
      }
    }
    ```
- **Extraction Logic:**
  - Token Breakdown: `input`, `output`, `cacheRead` (`cached`), `cacheWrite` (`cache_creation`), `reasoning`. Total tokens = `input + output + cacheRead`. Cost is calculated per turn to accurately price mixed-model sessions.

---

### 11. DeepSeek Harness (`dsh`)

- **Root Directories:** [`main.py:297-298`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L297-L298), [`main.py:4349-4452`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L4349-L4452)
  - `~/.dsh/sessions/<slugged-cwd>/<sessionId>/session.jsonl.zstd` (Zstandard compressed)
  - Plugin lifecycle sidecar: `~/.tokentelemetry/dsh_lifecycle.jsonl`
- **JSONL Schema (inside .zstd):**
  - Header:
    ```json
    {
      "type": "session",
      "version": 0,
      "id": "session-parent",
      "cwd": "/path/to/project",
      "createdAt": 1786806413737,
      "delegationDepth": 0,
      "agentPreset": "standard",
      "origin": "subagent",
      "parentSession": "session-parent"
    }
    ```
  - Event Stream:
    ```json
    {"type": "request/context", "time": 1786850753000, "data": {"provider": "cerebras", "model": "zai-glm-4.7"}}
    {"type": "assistant/chunk", "time": 1786850753001, "data": {"turn": 1, "step": 1, "chunk": {"type": "usage", "usage": {"inputTokens": 1000, "outputTokens": 200}}}}
    {"type": "assistant/message", "time": 1786850753002, "data": {"turn": 1, "step": 1, "usage": {"inputTokens": 1000, "outputTokens": 200}}}
    ```
- **Extraction & Delegation Logic:**
  - Usage Deduplication: `assistant/chunk` and `assistant/message` repeat the same `(turn, step)` usage; parser dedupes by turn/step key.
  - Delegation: Sessions with `origin == "subagent"` and `parentSession` matching a parent session are folded directly into the parent's `delegation` block (`subagents`, `delegated_total`, `delegated_cost`), rather than surfacing as top-level sessions.

---

### 12. Meta Muse Code & Prime Agent

- **Root Directories:** [`main.py:485-490`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L485-L490), [`main.py:517-654`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L517-L654), [`main.py:719-799`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L719-L799)
  - Muse: `~/.muse/sessions/*/*/*/*/session.jsonl` (or `TT_MUSE_SESSIONS_DIR`)
  - Prime: `~/.prime/sessions/*.jsonl` (or `TT_PRIME_SESSIONS_DIR` / `PRIME_AGENT_SESSION_DIR`)
- **Schemas:**
  - Muse JSONL line:
    ```json
    {
      "recorded_at": 1786806413737000,
      "payload": {
        "event": {
          "model": "llama-3.3-70b-versatile",
          "usage": {
            "input_tokens": 500,
            "output_tokens": 100,
            "cache_read_tokens": 200,
            "cache_write_tokens": 50,
            "reasoning_tokens": 20
          },
          "child_session_log_path": "subagent_1/session.jsonl"
        }
      }
    }
    ```
  - Prime Tree: JSONL lines have `id`, `parentId`, `type: "child_usage_attributed"`, `aggregateUsage`.
- **Extraction & Delegation Logic:**
  - Muse child transcripts referenced in `child_session_log_path` are resolved relative to the parent directory and rolled up into parent `delegation.subagents` and `delegated_*` buckets.
  - Prime reconstructs the active leaf-to-root branch in the in-file session tree.

---

### 13. Qwen Code (`qwen`) & Vibe (`vibe`)

- **Root Directories:** [`main.py:280-281`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L280-L281), [`main.py:6622-6693`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L6622-L6693)
  - Qwen: `~/.qwen/projects/*/chats/*.jsonl`
  - Vibe: `~/.vibe/logs/session/*.json`
- **Schemas & Extraction:**
  - Qwen: Assistant lines contain `model`, `usage: {input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens}`. Skills detected from `tool_use` `name: "activate_skill"`.
  - Vibe: `metadata.stats: {session_prompt_tokens, session_completion_tokens, context_tokens, session_total_llm_tokens}`.

---

## Token Pricing Engine (`pricing.py`) Specifications

The pricing subsystem ([`pricing.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py)) computes USD cost per session:

1. **Two-Tier Lookup ([`pricing.py:354-370`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L354-L370)):**
   - Tier 1: `(provider.lower(), model_id.lower())` in `PRICING_BY_PROVIDER` (from `pricing_data.json` or inline overrides).
   - Tier 2: `model_id.lower()` in `PRICING` (flat direct pricing) or prefix fuzzy matching.
   - Default fallback: `PRICING["_default"]` (`{"in": 2.00, "out": 10.00, "cached_read": 0.50}`).

2. **Cost Calculation Formula ([`pricing.py:390-409`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L390-L409)):**
   $$\text{Cost} = \left(\frac{\text{Input Tokens}}{10^6} \times R_{\text{in}}\right) + \left(\frac{\text{Output Tokens}}{10^6} \times R_{\text{out}}\right) + \left(\frac{\text{Cumulative Cache Read Tokens}}{10^6} \times R_{\text{cached}}\right) + \left(\frac{\text{Cache Creation Tokens}}{10^6} \times 1.25 \times R_{\text{in}}\right) + \left(\frac{\text{Cache Creation 1h Tokens}}{10^6} \times 2.0 \times R_{\text{in}}\right)$$

3. **Special Pricing Modes ([`pricing.py:316-352`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L316-L352)):**
   - **Subscription Endpoints & Models:** Cost is $0.00 (marginal cost tracked under flat monthly billing).
   - **Local / Ollama Models:** Priced by hardware electricity draw:
     $$\text{Cost}_{\text{electricity}} = \left(\frac{\text{Output Tokens}}{\text{Tokens Per Second}}\right) \times \left(\frac{\text{Watts}}{3600 \times 1000}\right) \times \text{kWh Rate}$$

---

## Go Port Architecture Recommendations

When implementing the single deployable Go binary:

1. **Parser Interface & Registry:**
   Define a unified `AgentScanner` interface:
   ```go
   type Session struct {
       ID               string                 `json:"id"`
       Agent            string                 `json:"agent"`
       Project          string                 `json:"project"`
       Timestamp        time.Time              `json:"timestamp"`
       Display          string                 `json:"display"`
       Model            string                 `json:"model"`
       Tokens           TokenUsage             `json:"tokens"`
       Cost             float64                `json:"cost"`
       Delegation       *DelegationMeta        `json:"delegation,omitempty"`
       ParentSessionID  *string                `json:"parent_session_id,omitempty"`
       ChildSessionIDs  []string               `json:"child_session_ids,omitempty"`
       MCPTools         []string               `json:"mcp_tools"`
       ToolCounts       map[string]int         `json:"tool_counts,omitempty"`
       SkillsUsed       []SkillUsage           `json:"skills_used,omitempty"`
   }

   type TokenUsage struct {
       Input            int64   `json:"input"`
       Output           int64   `json:"output"`
       Cached           int64   `json:"cached"`
       CacheCreation    int64   `json:"cache_creation"`
       CacheCreation1h  int64   `json:"cache_creation_1h,omitempty"`
       Reasoning        int64   `json:"reasoning,omitempty"`
       Total            int64   `json:"total"`
       Cost             float64 `json:"cost"`
       DelegatedInput   int64   `json:"delegated_input,omitempty"`
       DelegatedOutput  int64   `json:"delegated_output,omitempty"`
       DelegatedCached  int64   `json:"delegated_cached,omitempty"`
       DelegatedCreate  int64   `json:"delegated_cache_creation,omitempty"`
   }
   ```

2. **Concurrency & Safe SQLite Access:**
   - Use `modernc.org/sqlite` (pure Go, CGO-free) with `?mode=ro&_timeout=1000` to read SQLite stores (`opencode.db`, `hermes state.db`, `cline sessions.db`, `antigravity *.db`) concurrently without locking active agents.
   - Use `klauspost/compress/zstd` for streaming decompression of `.dsh/sessions/*/*/session.jsonl.zstd`.

3. **Incremental Scan Caching:**
   - Replicate `scan_cache.py` by persisting an SQLite or bbolt mtime cache (`~/.tokentelemetry/cache.db`) so sub-millisecond query responses are maintained across thousands of sessions.
