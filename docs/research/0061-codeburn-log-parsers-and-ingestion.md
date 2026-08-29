# Research: Codeburn Log Parsers and Provider Ingestion Engine

**Document ID:** `0061-codeburn-log-parsers-and-ingestion`  
**Related Ticket:** GitHub Issue #61  
**Target Repository:** `repositories/codeburn`  
**Status:** Complete  

---

## 1. Executive Summary

`codeburn` implements a high-throughput, multi-source ingestion engine capable of parsing and normalizing log, database, and transcript streams from **41 different AI coding agents and LLM providers**. The engine architecture combines:
1. **Multi-Source Discovery & Probing:** Dynamic discovery across operating systems (macOS, Linux, Windows), supporting filesystem globbing, VS Code extension storage, JetBrains roots, SQLite stores, compressed archives (zstd), protobuf binaries, and live HTTP/RPC endpoints.
2. **High-Performance Parsing Pipeline:** Dual-mode parsing utilizing a zero-allocation buffer-level JSON/JSONL scanner (`src/parser.ts`), Node.js worker pools for multi-threaded bulk decodes (`src/parse-workers.ts`), and resilient, concurrency-safe SQLite readers with WAL and retry support (`src/sqlite.ts`, `src/providers/sqlite-session-parser.ts`).
3. **Stream Normalization & Turn Reconstruction:** Transforming raw, disordered, or streaming events into canonical `ParsedTurn` and `ProjectSummary` models with deduplication, message ID collapsing, tool and bash extraction, patch diff calculation, subagent lineage tracing, and cross-range PR spend attribution.
4. **Durable & Incremental Caching:** A multi-tier caching system (`src/session-cache.ts`) using filesystem fingerprints (inode, mtime, size) and environment hashes to support monotonic aggregations even when host tools prune historical records.

---

## 2. Supported Providers and Log/Transcript Formats

`codeburn` catalogs providers into **Core Providers** (eagerly loaded) and **Lazy Providers** (`src/providers/index.ts:196-254`).

### Comprehensive Catalog of Supported Providers

| Provider Name | Display Name | Source File | Log / Storage Format | Discovery Path(s) & Environment Overrides |
| :--- | :--- | :--- | :--- | :--- |
| **claude** | Claude | `src/providers/claude.ts` | JSONL (`<uuid>.jsonl`) + JSON metadata | CLI: `~/.claude/projects/<slug>/` (`CLAUDE_CONFIG_DIR`, `CLAUDE_CONFIG_DIRS`). Desktop (Cowork): `Library/Application Support/Claude/local-agent-mode-sessions/<appId>/<wsId>/local_<sessionId>/` (`CODEBURN_DESKTOP_SESSIONS_DIR`). |
| **codex** | OpenAI Codex | `src/providers/codex.ts` | JSONL rollouts (`rollout-*.jsonl`) | `~/.codex/sessions/YYYY/MM/DD/` and `~/.codex/archived_sessions/` (`CODEX_HOME`). |
| **copilot** | GitHub Copilot | `src/providers/copilot.ts` | SQLite (`agent-traces.db`, `session-store.db`) & JSONL (`events.jsonl`, `session-state`) | VS Code globalStorage `agent-traces.db` (`CODEBURN_COPILOT_OTEL_DB`), CLI `~/.copilot/session-state/` (`CODEBURN_COPILOT_SESSION_STATE_DIR`), JetBrains `$XDG_CONFIG_HOME/github-copilot/` (`CODEBURN_COPILOT_JETBRAINS_DIR`). |
| **cursor** | Cursor | `src/providers/cursor.ts` | SQLite (`state.vscdb`) | `Cursor/User/globalStorage/state.vscdb` & `Cursor/User/workspaceStorage/<hash>/`. |
| **cursor-agent** | Cursor Agent | `src/providers/cursor-agent.ts` | Plaintext transcripts (`.txt`) + SQLite (`ai-code-tracking.db`) | `~/.cursor/projects/<project>/transcripts/<id>.txt` and `~/.cursor/ai-tracking/ai-code-tracking.db`. |
| **antigravity** | Antigravity | `src/providers/antigravity.ts` | Protobuf (`.pb`), SQLite (`.db`), and Live Language Server RPC | `~/.gemini/antigravity/conversations/`, `~/.gemini/antigravity-cli/conversations/`, `~/.gemini/antigravity-ide/conversations/`. |
| **hermes** | Hermes | `src/providers/hermes.ts` | SQLite databases + ledger | `~/.hermes/` (`HERMES_HOME`), profile databases. |
| **pi** / **omp** | Pi / Oh My Pi | `src/providers/pi.ts` | JSONL sessions (`*.jsonl`) | `~/.pi/agent/sessions/` and `~/.omp/agent/sessions/`. |
| **cline** | Cline | `src/providers/cline.ts` | JSON (`ui_messages.json`, `api_conversation_history.json`) | VS Code globalStorage `saoudrizwan.claude-dev/tasks/<id>/` and `~/.cline/data`. |
| **cline-cli** | Cline CLI | `src/providers/cline-cli.ts` | JSON tasks | `~/.cline/data/tasks/<id>/`. |
| **roo-code** | Roo Code | `src/providers/roo-code.ts` | JSON tasks | VS Code globalStorage `rooveterinaryinc.roo-cline/tasks/<id>/`. |
| **kilo-code** | KiloCode | `src/providers/kilo-code.ts` | JSON tasks & SQLite (`kilo*.db`) | VS Code globalStorage `kilocode.kilo-code/tasks/` and `~/.local/share/kilo/`. |
| **ibm-bob** | IBM Bob | `src/providers/ibm-bob.ts` | JSON tasks | VS Code globalStorage `ibm.bob-code/tasks/`. |
| **kiro** | Kiro | `src/providers/kiro.ts` | JSON (`session.json`, `chat.json`) & JSONL (`messages.jsonl`, `cli-sessions/*.jsonl`) | `Kiro/User/globalStorage/kiro.kiroagent/`, `workspaceStorage/`, `~/.kiro/sessions/cli/` (`KIRO_HOME`). |
| **kimi** | Kimi | `src/providers/kimi.ts` | JSON / TOML (`kimi.json`, `sessions/*.json`) | `~/.kimi/` (`KIMI_SHARE_DIR`). |
| **kimicode** | Kimi Code | `src/providers/kimicode.ts` | JSONL wire log (`wire.jsonl`) + JSON (`state.json`) | `~/.kimi-code/sessions/<sessionId>/` (`KIMI_CODE_HOME`). |
| **gemini** | Gemini Code Assist | `src/providers/gemini.ts` | JSON chat transcripts (`session-*.json`) | `~/.gemini/tmp/<hash>/chats/session-*.json`. |
| **grok** | Grok Build | `src/providers/grok.ts` | JSON metadata (`summary.json`, `signals.json`) + JSONL (`updates.jsonl` ACP RPC) | `~/.grok/sessions/<encoded-cwd>/<uuid>/` (`GROK_HOME`). |
| **devin** | Devin | `src/providers/devin.ts` | JSON trajectories (`trajectory.json`) & SQLite (`sessions.db`) | `~/.devin/sessions/` and `~/.devin/sessions.db`. |
| **droid** | Droid | `src/providers/droid.ts` | JSONL (`session.jsonl`) + JSON (`settings.json`) | `~/.factory/sessions/<id>/` (`FACTORY_DIR`). |
| **dsh** | DeepSeek Harness | `src/providers/dsh.ts` | Compressed JSONL (`session.jsonl.zstd`) or plain (`session.jsonl`) | `~/.dsh/sessions/<encoded-cwd>/session-<uuid>/` (`DSH_HOME`). |
| **forge** | Forge | `src/providers/forge.ts` | SQLite database (`.forge.db`) | `~/.forge/.forge.db`. |
| **goose** | Goose | `src/providers/goose.ts` | SQLite database (`sessions.db`) | `~/.local/share/goose/sessions/sessions.db` (`GOOSE_PATH_ROOT`). |
| **lingtai-tui** | LingTai TUI | `src/providers/lingtai-tui.ts` | JSONL ledger (`ledger.jsonl`) + JSON (`manifest.json`) | `~/.lingtai/` or `~/.lingtai-tui/`. |
| **mistral-vibe** | Mistral Vibe | `src/providers/mistral-vibe.ts` | JSONL messages (`messages.jsonl`) + JSON (`meta.json`) | `~/.vibe/logs/session-*/`. |
| **mux** | Mux | `src/providers/mux.ts` | JSONL messages (`messages.jsonl`) | `~/.mux/projects/<project>/threads/<threadId>/` (`MUX_ROOT`, `CODEBURN_MUX_DIR`). |
| **openclaw** | OpenClaw | `src/providers/openclaw.ts` | JSONL transcripts (`*.jsonl`) + JSON index (`sessions.json`) | `~/.openclaw/agents/<agentId>/sessions/`. |
| **openclaude** | OpenClaude | `src/providers/openclaude.ts` | JSONL transcripts (`*.jsonl`) | `~/.openclaude/projects/<slug>/<uuid>.jsonl` (`CODEBURN_OPENCLAUDE_DIR`). |
| **open-design** | Open Design | `src/providers/open-design.ts` | JSONL events (`*.jsonl`) | `~/.open-design/sessions/` (`CODEBURN_OPEN_DESIGN_DIR`). |
| **opencode** | OpenCode | `src/providers/opencode.ts` | SQLite (`opencode*.db`) & JSON files (`storage/session/*.json`) | `~/.local/share/opencode/` (`OPENCODE_DATA_DIR`, `OPENCODE_DB_PREFIX`). |
| **qwen** | Qwen Code | `src/providers/qwen.ts` | JSONL sessions (`*.jsonl`) | `~/.qwen/projects/<slug>/sessions/` (`QWEN_DATA_DIR`). |
| **quickdesk** | Quickdesk | `src/providers/quickdesk.ts` | JSONL metrics (`metrics-*.jsonl`) & SQLite (`quickwork.db`) | `~/.quickwork/` (`QUICKWORK_HOME`). |
| **zerostack** | Zerostack | `src/providers/zerostack.ts` | JSON sessions (`*.json`) | `~/.local/share/zerostack/sessions/` (`ZS_DATA_DIR`). |
| **warp** | Warp | `src/providers/warp.ts` | SQLite (`warp.sqlite`) | `~/Library/Group Containers/2BBY89MBSN.dev.warp/warp.sqlite`. |
| **vercel-gateway** | Vercel AI Gateway | `src/providers/vercel-gateway.ts` | HTTP REST API / JSON report | `https://ai-gateway.vercel.sh/v1/report` (`AI_GATEWAY_API_KEY`, `VERCEL_OIDC_TOKEN`). |
| **zcode** | ZCode | `src/providers/zcode.ts` | SQLite database (`db.sqlite`) | `~/.zcode/cli/db/db.sqlite`. |
| **zed** | Zed | `src/providers/zed.ts` | SQLite (`threads.db`) with zstd-compressed JSON blobs | `Zed/threads/threads.db`. |
| **codebuff** | Codebuff | `src/providers/codebuff.ts` | JSON chat history (`chat-messages.json`) | `~/.config/manicode/`, `manicode-dev/`, `manicode-staging/`. |
| **codewhale** | CodeWhale | `src/providers/codewhale.ts` | JSON / JSONL sessions (`*.json`, `*.jsonl`) | `~/.codewhale/sessions/`. |
| **crush** | Crush | `src/providers/crush.ts` | SQLite databases discovered via JSON registry (`projects.json`) | `~/.local/share/crush/projects.json` (`CRUSH_GLOBAL_DATA`). |

---

## 3. Ingestion Architecture & Parsing Implementation

### 3.1 Top-Level Ingestion Pipeline

The entry point for ingestion is `parseAllSessions()` in `src/parser.ts:5180`. The flow executes as follows:
1. **Discovery Phase (`src/providers/index.ts:279-294`):**
   - Calls `discoverAllSessions(providerFilter)`.
   - Executes `safeDiscoverSessions` concurrently over all registered providers (`src/providers/index.ts:264-277`) with exception isolation to prevent a single corrupted directory from failing the scan.
2. **Reconciliation & Cache Checking (`src/parser.ts:3323-3390`):**
   - Fingerprints discovered paths using `fingerprintFile()` (storing inode, device, mtime, size) (`src/session-cache.ts:40-100`).
   - Evaluates whether files are unchanged, changed, or removed using `reconcileFile()`.
3. **Worker Pool Parallelism (`src/parse-workers.ts:43-240`):**
   - Multi-gigabyte single-file transcripts (such as OpenAI Codex rollouts) are scheduled onto worker threads using `ParseWorkerPool` and `parseFilesInOrder()` (`src/parser.ts:3440-3468`).
   - Results are verified for deduplication consistency before main-thread cache installation (`src/parser.ts:3494-3521`).
4. **Serial In-Process Streaming Parsers:**
   - Providers implement `SessionParser.parse()` returning an `AsyncGenerator<ParsedProviderCall>` (`src/providers/types.ts:27-29`).
5. **Turn Normalization & Cache Persistence (`src/parser.ts:3531-3600`):**
   - Converts `ParsedProviderCall[]` to canonicalized `CachedTurn[]`.
   - Performs durable union merges for append-only / external SQLite providers (`src/parser.ts:3560-3592`).

---

### 3.2 Decoding Implementations & Stream Handling

#### A. Zero-Allocation Byte Scanner (`src/parser.ts:175-940`)
For high-volume JSONL log parsing (such as Claude Code and OpenClaude), `codeburn` avoids standard `JSON.parse` across multi-megabyte lines (which frequently contain giant tool outputs or base64 blobs):
- Lines exceeding `LARGE_JSONL_LINE_BYTES` (32 KB) enter `parseLargeJsonl()` (`src/parser.ts:575-630`).
- Implements `extractObjectFields()` (`src/parser.ts:529-570`) to perform a single forward pass scanning raw bytes for required keys (`type`, `timestamp`, `sessionId`, `cwd`, `gitBranch`, `message`, `attachment`, `isSidechain`) without allocating intermediate objects.
- Extracts token counts and advisor iterations directly from byte bounds via `findJsonContainerEnd()` (`src/parser.ts:299-304`), `readJsonNumberField()` (`src/parser.ts:322-328`), and `extractLargeToolBlocks()` (`src/parser.ts:389-434`).

#### B. Resilient SQLite Parser Architecture (`src/sqlite.ts` & `src/providers/sqlite-session-parser.ts`)
For SQLite-backed providers (Cursor, Copilot, Goose, Forge, OpenCode, KiloCode, ZCode, Zed, Crush, Warp, Hermes):
- Opens databases in readonly mode with `SQLITE_OPEN_READONLY | SQLITE_OPEN_URI` and WAL concurrency (`src/sqlite.ts:120-170`).
- Implements `rethrowBusy` and retry loops to handle concurrent writer locks without corrupting read transactions (`src/sqlite.ts:80-110`).
- Decodes typed blobs using `blobToText()` (`src/sqlite.ts:200-220`), handling raw UTF-8 buffers, zero-copy subarrays, and zstd compressed binary columns.

#### C. Frame-by-Frame Zstandard Streaming Decompressor (`src/providers/dsh.ts:56-99`)
For DeepSeek Harness (`dsh`), log files (`session.jsonl.zstd`) consist of concatenated individual zstd frames:
- Implements `scanZstdFrames()` (`src/providers/dsh.ts:56-99`) to parse the 4-byte magic (`0xfd2fb528`), descriptor headers, block headers, and checksums.
- Decompresses frames iteratively using `zstdDecompressSync`, handling torn frames from interrupted runs gracefully without rejecting valid prior frames.

---

### 3.3 Core Data Structures

1. **`SessionSource` (`src/providers/types.ts:3-25`):**
   Describes discovered session targets (file path, project name, provider name, source labels, agent metadata, durability markers).
2. **`ParsedProviderCall` (`src/providers/types.ts:31-97`):**
   Canonical representation of a single LLM request/response cycle:
   - Tokens: `inputTokens`, `outputTokens`, `cacheCreationInputTokens`, `cacheReadInputTokens`, `cachedInputTokens`, `reasoningTokens`.
   - Cost: `costUSD`, `costIsEstimated`, `nanoAiu`.
   - Execution Context: `tools`, `bashCommands`, `skills`, `subagentTypes`, `timestamp`, `speed`, `deduplicationKey`, `locAdded`, `locRemoved`, `editFailed`, `workingDirectory`.
3. **`ParsedTurn` (`src/types.ts:88-107`):**
   A user-assistant conversational turn grouping:
   - `userMessage`: The input prompt triggering the turn.
   - `assistantCalls`: Ordered list of `ParsedApiCall`.
   - `gitBranch`: Git branch active during turn.
   - `prRefs`: Pull request URLs referenced or generated.
   - `spawnToolUseIds`: Identifiers of subagents spawned.
4. **`CachedTurn` & `SessionCache` (`src/session-cache.ts:110-180`):**
   The durable on-disk cache schema mapping provider names and file paths to structured turns, MCP inventories, and parent/child lineages.

---

## 4. Stream Normalization into Turn and Session Events

The engine normalizes raw event streams through seven pipeline stages:

### 4.1 Streaming Deduplication & Message Collapsing
- **Streaming Chunks:** In streaming protocols (Claude, Grok ACP, Copilot), the assistant emits partial message updates sharing one `message.id`.
- `dedupeStreamingMessageIds()` (`src/parser.ts:1526-1548`) scans entries, finds the first and last occurrence for each message ID, retains the initial timestamp (to preserve prompt start latency), and captures the final usage/content block.
- `seenKeys` sets ensure calls processed across multiple files or re-parsed sessions are never double-counted (`src/parser.ts:3421-3428`).

### 4.2 Turn Boundary Detection and Grouping (`src/parser.ts:1550-1622`)
- Turn demarcation begins whenever a `user` entry with non-empty text is encountered.
- Assistant calls, tool executions, and subagent invocations occurring prior to the next user entry are accumulated into that turn's `assistantCalls`.
- **Advisor Sub-calls:** Special advisor tool invocations (`/advisor`) recorded in `message.usage.iterations` are split into distinct `ParsedApiCall` records attributed to the advisor model (`src/parser.ts:1465-1524`).

### 4.3 Tool Normalization, Diff LOC Extraction & Command Classification
- Tool names from provider-specific dialects (e.g. `exec_command`, `str_replace`, `developer__shell`, `runCommand`) are mapped to canonical identifiers (`Bash`, `Edit`, `Read`, `Grep`, `Glob`, `Agent`, `WebSearch`) (`src/classifier.ts:19-24`, `src/providers/*.ts`).
- **Diff LOC Counter:** `countStructuredPatchLoc` (`src/parser.ts:1261-1275`) and `countUnifiedDiffLoc` (`src/providers/codex.ts:115-124`) inspect hunk additions (`+`) and removals (`-`) to compute `locAdded` and `locRemoved`.
- **Bash Command Extraction:** `extractBashCommands()` (`src/bash-utils.ts`) unwraps compound shell scripts (`bash -c "..."`, pipes, subshells) to extract underlying CLI tool invocations and recognize embedded MCP/Skill executions.

### 4.4 Multi-Agent & Subagent Lineage Resolution
- **Claude Sidechains:** Subagents spawned via `Agent` or `Task` tool calls record the spawned agent's ID in `toolUseResult.agentId`. `collectSessionMeta()` (`src/parser.ts:1304-1356`) maps parent spawn tool use IDs to child session IDs.
- **Kimi Code & OMP:** Subagent transcripts (e.g. Oh My Pi crewmates, Kimi Code `state.json` `parentAgentId`) carry explicit lineage metadata which is stored in `CachedFile.lineage` (`src/parser.ts:3534-3543`, `src/providers/kimicode.ts:16-22`).
- Turn grouping folds sidechains back into the parent turn that spawned them for PR-level and feature-level cost attribution (`src/sessions-report.ts`).

### 4.5 Project Path Canonicalization & Git Worktrees (`src/parser.ts:124-173`)
- `resolveCanonicalProjectPath()` checks `.git` directories and walks linked worktrees (`gitdir: .../.git/worktrees/<name>`) to canonicalize worktree sessions back to the root repository project key.
- Normalizes Windows and POSIX path separators to generate unified cross-provider project identifiers (`src/parser.ts:80-89`).

### 4.6 Cost and Token Accounting Normalization
- Token usage is normalized into: `inputTokens`, `outputTokens`, `cacheCreationInputTokens`, `cacheReadInputTokens`, `cachedInputTokens`, and `reasoningTokens` (`src/types.ts:1-9`).
- `billableOutputTokens()` (`src/models.js`) resolves discrepancies where some models include reasoning tokens within output tokens while others report them separately.
- `calculateCost()` (`src/models.js`) evaluates pricing overrides, 5m/1h ephemeral prompt cache tiers, web search request fees, and fast/standard generation speeds.

---

## 5. Key File Citations & Reference Matrix

| Component | Source File | Line Range | Key Identifier / Functionality |
| :--- | :--- | :--- | :--- |
| Provider Registry & Discovery | `src/providers/index.ts` | 196–294 | `CORE_PROVIDERS`, `LAZY_PROVIDERS`, `discoverAllSessions` |
| Main Parser Engine | `src/parser.ts` | 175–940, 1550–1622, 5180+ | Zero-alloc JSONL scanner, turn grouping, `parseAllSessions` |
| Worker Pool Parallelism | `src/parse-workers.ts` | 43–240 | `ParseWorkerPool`, background worker threading |
| Resilient SQLite Architecture | `src/sqlite.ts` | 80–220 | WAL mode, busy retries, blob UTF-8 decoding |
| Session Caching & Fingerprinting | `src/session-cache.ts` | 40–180 | Inode/mtime fingerprinting, `CachedTurn`, `SessionCache` |
| Claude & Cowork Provider | `src/providers/claude.ts` | 1–350 | Claude CLI & Cowork desktop transcript parsing |
| OpenAI Codex Provider | `src/providers/codex.ts` | 115–1250 | Multi-gigabyte JSONL rollout parser & diff tracking |
| GitHub Copilot Provider | `src/providers/copilot.ts` | 1–970 | SQLite `agent-traces.db`, OTel, JetBrains, nano-AIU |
| Cursor & Cursor Agent | `src/providers/cursor.ts`, `cursor-agent.ts` | 1–950 | SQLite `state.vscdb`, bubble turn reconstruction |
| Antigravity Protobuf/RPC | `src/providers/antigravity.ts` | 1–850 | Protobuf wire decode, LS RPC live monitoring |
| DeepSeek Harness (zstd) | `src/providers/dsh.ts` | 56–99 | Frame-by-frame zstandard decompressor |
