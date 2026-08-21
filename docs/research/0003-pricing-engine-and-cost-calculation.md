# Reverse-Engineered Architecture: Pricing Engine, Model Resolution, and Cost Calculation Logic

**Research Issue:** #3 (Part of Map #1)  
**Target Repository:** `repositories/tokentelemetry/backend/`  
**Date:** 2026-08-21  

---

## 1. Executive Summary

TokenTelemetry's pricing and cost-calculation engine is built on a **local-first, two-tier architecture** designed to estimate dollar costs across diverse LLM providers, multi-agent frameworks, local hardware runs, and flat subscription plans without performing any network I/O at runtime.

The core responsibilities of this subsystem include:
1. **Pricing Dataset Loading & Overlay:** Maintaining authoritative hand-curated rates in Python dicts while overlaying a larger build-time dataset (`pricing_data.json` scraped from `models.dev/api.json`) during module import.
2. **Model Normalization & Fuzzy Resolution:** Resolving arbitrary model identifiers, namespace-prefixed strings, and provider overrides with longest-prefix fuzzy matching.
3. **Execution Context Short-Circuiting:** Intercepting flat-rate subscription models/endpoints ($0 marginal cost) and self-hosted/local models (priced by hardware wattage and electricity tariffs rather than API tokens).
4. **Multi-Rate Token Cost Calculation:** Accurately costing input tokens, output tokens, prompt-cache reads, and multi-tier prompt-cache writes (5-minute vs 1-hour TTLs).
5. **Session-Level & Subagent Cost Rollups:** Aggregating costs across heterogeneous subagents (preserving the count-once invariant) and categorizing cost provenance via explicit metadata tags (`cost_status`).

---

## 2. Pricing Data Architecture and Loading

### 2.1 File Structure and Roles

- [`backend/pricing.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py): Primary pricing module. Houses curated static tables, runtime lookup, overlay loader, and `calculate_cost()`.
- [`backend/pricing_data.json`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing_data.json): Committed static JSON snapshot generated at build/CI time.
- [`backend/pricing_sync.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing_sync.py): Maintainer/CI-only sync utility to regenerate `pricing_data.json` from `https://models.dev/api.json`.
- [`backend/power_config.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/power_config.py): Hardware power configuration, local inference detection, and electricity tariff formulas.
- [`backend/billing_mode.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/billing_mode.py): Agent-level billing mode inference (`subscription`, `api`, `local`, `unknown`).
- [`backend/billing_route.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/billing_route.py): Drain-priority multi-bucket credit router (handling task-type distinctions between `interactive` and `programmatic`).

### 2.2 In-Memory Data Structures

Prices are expressed in **USD per 1 Million tokens (1 MTok)**:

1. **Flat Fallback Table (`PRICING`)** ([`pricing.py:38-148`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L38-L148)):
   - Key: Lowercase model identifier (e.g., `"claude-sonnet-4-6"`, `"gpt-5.4"`, `"gemini-3.1-pro"`).
   - Value: `{"in": float, "out": float, "cached_read": float | None}`.
   - Includes baseline fallback: `PRICING["_default"] = {"in": 2.00, "out": 10.00, "cached_read": 0.50}` ([`pricing.py:147`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L147)).
2. **Provider-Keyed Table (`PRICING_BY_PROVIDER`)** ([`pricing.py:153-196`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L153-L196)):
   - Key: Tuple of `(provider_lower, model_id_lower)` (e.g., `("together", "deepseek-v4-pro")`, `("groq", "openai/gpt-oss-20b")`).
   - Value: `{"in": float, "out": float, "cached_read": float | None}`.
   - Preserves price discrepancies across aggregators (e.g., DeepSeek v4 Pro direct $1.74/$3.48 vs Together $2.10/$4.40).

### 2.3 Build-Time Sync & In-Place Module Overlay

- **Sync Pipeline ([`pricing_sync.py:114-154`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing_sync.py#L114-L154)):**
  - Fetches `https://models.dev/api.json` and flattens provider/model tuples into string keys separated by `\x00` (`_PROVIDER_SEP = "\x00"`).
  - Aliases provider keys (`"fireworks-ai"` -> `"fireworks"`, `"together-ai"` -> `"together"`).
  - Enforces sanity boundaries: drops entries where rates are `< 0.0` or `> 10,000.0` USD/MTok ([`pricing_sync.py:59-74`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing_sync.py#L59-L74)).
- **Zero Network I/O Guarantee ([`pricing.py:25-32`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L25-L32), [`test_pricing_data.py:29-42`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/test_pricing_data.py#L29-L42)):**
  - Runtime strictly reads the local `pricing_data.json` from the backend directory.
  - Sockets are never opened during import or execution.
- **Overlay Precedence ([`pricing.py:222-269`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L222-L269)):**
  - Executed at module import via `_load_bundled_pricing()`.
  - **Inline curated entries always win.** If `key in PRICING` or `tup in PRICING_BY_PROVIDER`, the overlay entry is skipped.
  - Overlay entries expand the catalog with the long tail of models without risking regressions on hand-tuned prices.
  - Any parsing errors, schema mismatches, or missing files fail silently to preserve static fallback tables.

---

## 3. Model Normalization, Alias Matching, and Resolution Hierarchy

When `calculate_cost()` is called with `model_name` and optional `provider`, resolution follows a 5-step waterfall ([`pricing.py:354-389`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L354-L389)):

```mermaid
flowchart TD
    A[Call calculate_cost] --> B{Subscription endpoint/model?}
    B -- Yes --> C[Return $0.00]
    B -- No --> D{Local Session?}
    D -- Yes --> E[Compute electricity cost via power_config]
    D -- No --> F[Normalize model: lowercase + strip aggregator prefix]
    F --> G{Provider supplied?}
    G -- Yes --> H[Lookup PRICING_BY_PROVIDER: provider, normalized_model]
    G -- No --> I[Lookup PRICING: normalized_model]
    H -- Found --> J[Extract in/out/cache rates]
    H -- Miss --> I
    I -- Found --> J
    I -- Miss --> K[Fuzzy match: check keys sorted by len desc]
    K -- Found --> J
    K -- Miss --> L{local_power_enabled?}
    L -- Yes --> E
    L -- No --> M[Fallback to PRICING['_default']]
    M --> J
    J --> N[Apply Token Cost Formula]
```

### 3.1 Normalization (`_normalize_model_id`)
[`pricing.py:273-282`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L273-L282):
```python
def _normalize_model_id(model: str) -> str:
    m = model.lower().strip()
    for prefix in ("fireworks/", "together/", "openrouter/"):
        if m.startswith(prefix):
            m = m[len(prefix):]
            break
    return m
```

### 3.2 Resolution Steps

1. **Explicit Provider Lookup:**
   If `provider` is passed, checks `PRICING_BY_PROVIDER.get((provider.lower(), m_norm))`.
2. **Exact Model Lookup:**
   Checks `PRICING.get(m_norm)`.
3. **Longest-Key Substring Fuzzy Match:**
   If no exact match is found, tests keys in `PRICING` (excluding `_default`) sorted by length descending:
   ```python
   sorted_keys = sorted([k for k in PRICING.keys() if k != "_default"], key=len, reverse=True)
   for k in sorted_keys:
       if k in m_norm:
           config = PRICING[k]
           break
   ```
   *Rationale:* Descending length prevents short substrings (like `"gpt-5"`, `"claude-3"`) from prematurely matching specific variants (like `"gpt-5.5-pro"`, `"claude-3-5-sonnet"`).
4. **Local Power Fallback for Unpriced Models:**
   If no rate is found and `local_power_enabled()` is True (user configured power parameters in `~/.tokentelemetry/power.json`), it assumes the unpriced model is running on local hardware and prices by electricity.
5. **Static Default Fallback:**
   Falls back to `PRICING["_default"]` (`in: 2.00`, `out: 10.00`, `cached_read: 0.50`).

---

## 4. Cost Calculation Formulas and Token Semantics

Cost computation in `calculate_cost()` ([`pricing.py:285-409`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L285-L409)) operates on four distinct token streams.

### 4.1 Rate Derivation

- **Input Rate ($R_{in}$):** `config["in"]` (USD / 1M tokens)
- **Output Rate ($R_{out}$):** `config["out"]` (USD / 1M tokens)
- **Cache Read Rate ($R_{cached}$):**
  - If explicitly defined in entry: `config["cached_read"]`
  - If `None`: Defaults to $10\%$ of input rate ($R_{in} \times 0.10$) ([`pricing.py:394`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L394)).
- **Prompt-Cache Write Rate ($R_{write, 5m}$ & $R_{write, 1h}$):**
  - Follows Anthropic prompt caching pricing structure:
  - Standard 5-minute TTL: $R_{write, 5m} = R_{in} \times 1.25$ ($125\%$ of input rate).
  - 1-hour ephemeral TTL: $R_{write, 1h} = R_{in} \times 2.00$ ($200\%$ of input rate).

### 4.2 Cache Creation Token Partitioning

To avoid double-counting 1-hour writes against total cache writes:
$$\text{tokens}_{write, 1h} = \min(\text{cache\_creation\_1h\_tokens}, \text{cache\_creation\_tokens})$$
$$\text{tokens}_{write, 5m} = \text{cache\_creation\_tokens} - \text{tokens}_{write, 1h}$$

### 4.3 Total Cost Mathematical Formula

$$\text{Cost}_{\text{USD}} = \frac{\text{tokens}_{in}}{10^6} R_{in} + \frac{\text{tokens}_{out}}{10^6} R_{out} + \frac{\text{tokens}_{cached}}{10^6} R_{cached} + \frac{\text{tokens}_{write, 5m}}{10^6} R_{write, 5m} + \frac{\text{tokens}_{write, 1h}}{10^6} R_{write, 1h}$$

---

## 5. Local Hardware & Flat Subscription Overrides

Before token multiplication occurs, `calculate_cost()` evaluates short-circuiting rules in [`power_config.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/power_config.py):

### 5.1 Flat Subscription Short-Circuiting ($0.00 Marginal Cost)

- **Subscription Endpoints ([`power_config.py:277-298`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/power_config.py#L277-L298)):**
  Matches `endpoint` against `subscriptionEndpoints` in `power.json` (case- and scheme-insensitive substring match). E.g., `https://ollama.com` or custom proxy URLs.
- **Subscription Models ([`power_config.py:300-310`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/power_config.py#L300-L310)):**
  Matches `model_name` against `subscriptionModels` in `power.json` (case-insensitive exact match).
- Returns `0.0` immediately.

### 5.2 Confirmed-Local Session Detection & Electricity Pricing

A session is identified as local if any of the following hold ([`power_config.py:325-357`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/power_config.py#L325-L357)):
1. `billing_mode == "local"`
2. `endpoint` is loopback (`localhost`, `127.0.0.1`, `0.0.0.0`, `::1`) or matches `localEndpoints` in `power.json`.
3. `provider` is in `LOCAL_PROVIDERS` (`{"ollama", "lmstudio", "llama.cpp", "vllm", "localai", "jan", "gpt4all", "koboldcpp", "local", ...}`).

#### Electricity Formula ([`power_config.py:392-415`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/power_config.py#L392-L415)):
$$\text{gen\_seconds} = \frac{\text{output\_tokens}}{\text{tok\_per\_sec}}$$
$$\text{kWh} = \frac{\text{load\_watts} \times \text{gen\_seconds}}{3{,}600{,}000}$$
$$\text{Cost}_{\text{electricity}} = \text{kWh} \times \text{cost\_per\_kwh}$$

- **Throughput Inference (`tok_per_sec`):**
  - Uses measured throughput when session logs contain token latency (e.g. Hermes SQLite summary [`main.py:7216-7218`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L7216-L7218)).
  - Otherwise parses parameter count from model name via regex `r"(\d+(?:\.\d+)?)\s*b\b"` ([`power_config.py:363-389`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/power_config.py#L363-L389)):
    - $\le 1\text{B} \rightarrow 150 \text{ tok/s}$
    - $\le 4\text{B} \rightarrow 90 \text{ tok/s}$
    - $\le 8\text{B} \rightarrow 70 \text{ tok/s}$
    - $\le 14\text{B} \rightarrow 50 \text{ tok/s}$
    - $\le 34\text{B} \rightarrow 30 \text{ tok/s}$
    - $\le 70\text{B} \rightarrow 18 \text{ tok/s}$
    - $> 70\text{B} \rightarrow 10 \text{ tok/s}$
    - Unparseable fallback: `DEFAULT_TOK_PER_SEC = 30.0`
- **Dynamic Chip Power Detection:**
  Auto-detects Apple Silicon tier/watts via `power_meter.py` / `sysctl`, defaulting to 80 W and 0.15 USD/kWh.

---

## 6. Session Cost Calculation and Aggregation Mechanics

### 6.1 Scanner Integration & Turn-by-Turn Costing

Across `main.py` session scanners (Claude Code, Gemini, Codex, Hermes, Grok, Pi/DSH, Muse, etc.):
- **Claude Code & Muse Subagent Rollups:**
  Subagent transcripts (`subagents/agent-<agentId>.jsonl`) specify their own `message.model`. Because subagents often use smaller/cheaper models (e.g., `haiku-4-5`) while the parent runs `opus-4-7`, costing with the parent's model is explicitly avoided ([`DESIGN.md:34-35`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/DESIGN.md#L34-L35)). Each subagent file is priced independently and attached to parent `delegation.delegated_cost`.
- **Count-Once Invariant ([`DESIGN.md:94-109`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/DESIGN.md#L94-L109)):**
  - In frameworks where child subagents are independent sessions (OpenCode, Hermes), children are already counted in global totals. Parents only receive linking annotations (`parent_session_id`, `child_session_ids`), preventing double-counting.
  - In frameworks where subagents are nested files (Claude Code, Muse), child usage is summed into the parent's `delegated_*` fields.
- **Turn-by-Turn Cache Aggregation:**
  Scanners record `_cached_sum` (cumulative cache reads across all turns) alongside `cached` (the high-water-mark prefix length). For cost calculation, cumulative reads are costed.

### 6.2 Cost Provenance Attribution (`cost_status`)

Every session is tagged with an explicit `cost_status` string ([`main.py:7189-7268`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L7189-L7268)):
- `provider-reported`: Direct invoice cost from provider logs (e.g., Hermes `actual_cost_usd`).
- `provider-estimated`: Provider estimate preserved from logs.
- `tt-computed`: Calculated by TokenTelemetry's `calculate_cost()`.
- `zero-marginal`: Confirmed local model or flat subscription where marginal cost is truly $0.00.
- `unpriced`: TokenTelemetry could not price the model or session (rendered in UI as "not captured" rather than a misleading "$0.00").

### 6.3 Drain-Priority Multi-Bucket Routing (`billing_route.py`)

Handles complex provider policies where single agents drain multiple credit pools depending on task type ([`billing_route.py:1-49`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/billing_route.py#L1-L49)):
- **Task Type Classification:** Distinguishes `interactive` (terminal/editor) vs `programmatic` (CI, `claude -p`, SDK).
- **Date-Gated Pools:** E.g., Anthropic Agent-SDK split (`ANTHROPIC_SDK_SPLIT_DATE = 2026-06-15`), routing programmatic sessions to a dedicated `$20` / `$100` / `$200` monthly pool with `no_spillover=True`.
- **Copilot & Cursor AI Credit Pools:** Models included credits ($19–$39/mo for Copilot, $20–$200/mo for Cursor) vs usage overage.

### 6.4 Analytics Engine Aggregations (`/analytics`)

The `/analytics` endpoint ([`main.py:9930-10030`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9930-L10030)) merges historical SQLite data (`history_store.py`) with live in-flight sessions:
- Aggregates tokens, costs, energy (Wh), cloud savings ($), and CO2 emissions across:
  - `by_agent`
  - `by_model`
  - `by_day`
- **Accurate Cache Hit Rate:**
  $$\text{Cache Hit \%} = \frac{\text{cache\_reads}}{\text{input\_tokens} + \text{cache\_reads}} \times 100$$
  Uses `_cached_sum` (cumulative cache reads) instead of the high-water-mark `cached` to avoid under-reporting on long conversations.
- **Local vs Cloud Savings:**
  $$\text{Savings}_{\text{USD}} = \max(0.0, \text{Cost}_{\text{cloud\_ref}} - \text{Cost}_{\text{local\_electricity}})$$
  Where $\text{Cost}_{\text{cloud\_ref}}$ is computed via `calculate_cost()` using `referenceCloudModel` (default `claude-sonnet-4-6`).

---

## 7. Key File & Line Range Index

| Component | File Path | Key Line Ranges |
| :--- | :--- | :--- |
| Curated Flat Pricing | [`pricing.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py) | [Lines 38–148](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L38-L148) |
| Provider Pricing Overrides | [`pricing.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py) | [Lines 153–196](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L153-L196) |
| Bundled Overlay Loader | [`pricing.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py) | [Lines 199–270](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L199-L270) |
| Model Normalization & Fuzzy Resolution | [`pricing.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py) | [Lines 273–282](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L273-L282), [354–389](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L354-L389) |
| `calculate_cost()` Core Function | [`pricing.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py) | [Lines 285–409](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing.py#L285-L409) |
| Pricing Sync Script | [`pricing_sync.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing_sync.py) | [Lines 1–173](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/pricing_sync.py#L1-L173) |
| Local Session & Electricity Math | [`power_config.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/power_config.py) | [Lines 325–415](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/power_config.py#L325-L415) |
| Billing Mode Detection | [`billing_mode.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/billing_mode.py) | [Lines 40–146](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/billing_mode.py#L40-L146) |
| Multi-Bucket Drain Router | [`billing_route.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/billing_route.py) | [Lines 135–389](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/billing_route.py#L135-L389) |
| Cost Status & Session Cost Assignment | [`main.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py) | [Lines 7180–7268](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L7180-L7268) |
| Analytics & Savings Aggregation | [`main.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py) | [Lines 9930–10030](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/main.py#L9930-L10030) |
| Delegation Token Invariants | [`DESIGN.md`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/DESIGN.md) | [Lines 94–109](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/DESIGN.md#L94-L109) |
| Unit Tests for Cache Pricing | [`test_pricing.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/test_pricing.py) | [Lines 1–122](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/test_pricing.py#L1-L122) |
| Unit Tests for Overlay & Offline Import | [`test_pricing_data.py`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/test_pricing_data.py) | [Lines 1–131](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/tokentelemetry/backend/test_pricing_data.py#L1-L131) |
