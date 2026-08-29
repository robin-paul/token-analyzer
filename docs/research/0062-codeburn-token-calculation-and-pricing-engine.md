# Research: Codeburn Token Calculation, Pricing Catalogs, and Cost Engine

**Research Issue:** GitHub Issue #62  
**Target Repository:** `repositories/codeburn`  
**Target Output File:** `docs/research/0062-codeburn-token-calculation-and-pricing-engine.md`  
**Status:** Complete  

---

## 1. Executive Summary

`codeburn` implements a high-performance, local-first cost and token observability engine designed to parse logs and session stores from over 20 AI coding assistants (Claude Code, OpenAI Codex, GitHub Copilot, Cursor, Gemini CLI, Grok Build, Kimi Code, Kiro, Warp, Hermes, Antigravity, Droid, Qwen, Devin, etc.) without requiring network connectivity at query time.

The core architecture is structured around four subsystems:
1. **Multi-Provider Token Normalization & Accounting:** Normalizes disparate token semantics across providers into a uniform `TokenUsage` model. Resolves subtle vendor differences such as reasoning token inclusion/exclusion (preventing double-billing on OpenAI, Anthropic, and Copilot) and inclusive vs. exclusive prompt caching representations.
2. **Layered Pricing Catalog & Resolution Pipeline:** Employs a multi-tier resolution hierarchy spanning hand-curated built-in overrides, user overrides, live remote LiteLLM rate files with disk caching (24h TTL), build-time snapshot fallbacks, gap-filling catalogs from models.dev and OpenRouter, router prefix stripping, longest-prefix fuzzy matching, and suffix peeling.
3. **Multi-Tier Gross vs. Net Cost Engine:** Implements prompt caching cost dynamics (5-minute vs. 1-hour cache write TTLs, 10% cache read discounts, 125% cache write heuristics), fast inference multipliers, web search request fees, and dynamic prompt volume tiering (e.g., Grok 4.6 >200k threshold). Computes counterfactual local-model savings against baseline cloud models.
4. **Resilient Token Estimation & Fallback Heuristics:** Employs a standard 4-characters-per-token heuristic (`estimateTokensFromChars`) with explicit `costIsEstimated` metadata flags when provider logs omit token counts, support credit-to-dollar conversions (Kiro $0.04/credit, Copilot 1e9 nano-AIU = $0.01), and handles multi-turn token attribution (e.g., Droid turn-level remainder spreading).

---

## 2. Token Calculation, Normalization, and Semantics

### 2.1 Core Data Structures
- **`TokenUsage`** ([`src/types.ts:1-9`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/types.ts#L1-L9)):
  ```typescript
  export type TokenUsage = {
    inputTokens: number
    outputTokens: number
    cacheCreationInputTokens: number
    cacheReadInputTokens: number
    cachedInputTokens: number
    reasoningTokens: number
    webSearchRequests: number
  }
  ```
- **`ApiUsage` & `ApiUsageIteration`** ([`src/types.ts:24-61`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/types.ts#L24-L61)): Captures Claude Code top-level and advisor (`/advisor`) sub-turn iterations, including split ephemeral cache tiers (`ephemeral_5m_input_tokens`, `ephemeral_1h_input_tokens`) and server tool executions (`web_search_requests`, `web_fetch_requests`).
- **`ParsedApiCall` & `ParsedProviderCall`** ([`src/types.ts:109-170`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/types.ts#L109-L170), [`src/providers/types.ts:31-97`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/types.ts#L31-L97)): Carries call-level cost (`costUSD`), savings (`savingsUSD`), metadata flags (`costIsEstimated`, `isLocalSavings`, `supplementaryAccounting`), tool invocations, diff metrics (`locAdded`, `locRemoved`), and credit amounts (`nanoAiu`).

### 2.2 Reasoning Tokens & Billable Output Invariants
Providers differ fundamentally on whether reasoning/thinking tokens are included inside the reported `output_tokens` count or emitted as an independent additive bucket:
- **The Single Source of Truth (`billableOutputTokens`)** ([`src/models.ts:27-43`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L27-L43)):
  ```typescript
  const REASONING_INCLUDED_IN_OUTPUT = new Set(['claude', 'codex', 'copilot'])

  export function billableOutputTokens(provider: string, outputTokens: number, reasoningTokens: number): number {
    return REASONING_INCLUDED_IN_OUTPUT.has(provider) ? outputTokens : outputTokens + reasoningTokens
  }
  ```
  - **Claude / Anthropic:** Thinking tokens are included inside `output_tokens`.
  - **OpenAI / Codex:** `reasoning_output_tokens` are a subset of `output_tokens` (every Codex `token_count` satisfies `input + output == total`). Summing them would double-count both output tokens and billed costs ([`src/models.ts:28-31`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L28-L31), [`src/providers/codex.ts:1239-1250`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/codex.ts#L1239-L1250)).
  - **Copilot:** Per-request `token_details_json` prices `input/cache/output` with reasoning already embedded in turn output ([`src/models.ts:31-35`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L31-L35)).
  - **Gemini:** `thoughts` are reported separately, but billed by Google at the output rate; `calculateCost` folds thoughts into output while preserving `reasoningTokens` in reporting ([`src/providers/gemini.ts:122-135`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/gemini.ts#L122-L135)).
  - **Antigravity:** Decodes protobuf field 10 (`thinkingTokens`) and reconciles against total output ([`src/providers/antigravity.ts:810-824`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/antigravity.ts#L810-L824)).
  - **Grok:** Reports reasoning inside output on the wire; `src/providers/grok.ts:406-417` explicitly subtracts reasoning (`outputTokens = parsed.usage.output - reasoningTokens`) so downstream callers using `billableOutputTokens` re-add it without distortion.
  - **Qwen:** Explicitly adds `thoughtsTokenCount` to candidate tokens ([`src/providers/qwen.ts:119-122`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/qwen.ts#L119-L122)).

### 2.3 Prompt Caching and Input Token Normalization
- **Anthropic / Claude Code Semantics:** `input_tokens` represents non-cached prompt tokens. `cache_read_input_tokens` represents cached tokens read at a discount. Cache creation tokens are extracted via `extractClaudeCacheCreation()` ([`src/parser.ts:1166-1185`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/parser.ts#L1166-L1185)), handling split 5-minute vs. 1-hour ephemeral tiers.
- **OpenAI / Codex Semantics:** OpenAI `input_tokens` is cache-inclusive (includes cached tokens). Codeburn normalizes this to Anthropic semantics:
  - `uncachedInputTokens = Math.max(0, inputTokens - cachedInputTokens)` ([`src/providers/codex.ts:1197`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/codex.ts#L1197)).
  - Cache writes are carved out of uncached input: `cacheWriteInputTokens = Math.max(0, Math.min(cacheWriteTokens, uncachedInputTokens))` ([`src/providers/codex.ts:1202`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/codex.ts#L1202)).
  - Tokens are routed to the cache-write bucket **only** if the pricing catalog explicitly defines a cache-write rate (`cacheWriteCostIsExplicit`); otherwise they remain in plain input to avoid inventing surcharges ([`src/providers/codex.ts:1211-1214`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/codex.ts#L1211-L1214)).
- **GitHub Copilot:** `usage.inputTokens` is cache-inclusive. Net uncached input is computed via: `inputTokens = Math.max(0, delta('inputTokens') - cacheReadTokens - cacheWriteTokens)` ([`src/providers/copilot.ts:959-966`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/copilot.ts#L959-L966)).
- **Gemini:** `totalInput` includes `cached`; fresh input is normalized via `freshInput = Math.max(0, totalInput - totalCached)` ([`src/providers/gemini.ts:113-115`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/gemini.ts#L113-L115)).

---

## 3. Pricing Catalogs, Rate Tables, and Override Resolution

### 3.1 Catalog Sources and Build Pipeline
Codeburn combines four distinct pricing sources in priority order ([`scripts/bundle-litellm.mjs:5-19`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/scripts/bundle-litellm.mjs#L5-L19)):
1. **LiteLLM Primary Snapshot:** Fetched from `https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json` (`LITELLM_URL`, [`scripts/bundle-litellm.mjs:20`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/scripts/bundle-litellm.mjs#L20)).
2. **Manual Curated Overrides (`MANUAL_ENTRIES`):** Committed overrides for unreleased or unmerged models (e.g., `MiniMax-M2.7`, `deepseek-v4-flash`, `deepseek-v4-pro`, `claude-mythos-5`, `gpt-5.6-codex`) ([`scripts/bundle-litellm.mjs:39-57`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/scripts/bundle-litellm.mjs#L39-L57)).
3. **models.dev First-Party Catalog:** Scraped from `https://models.dev/api.json` filtered strictly to first-party makers (`MODELS_DEV_FIRST_PARTY`: `openai`, `anthropic`, `google`, `mistral`, `deepseek`, `xai`, `minimax`, `zhipuai`, `cohere`, etc.) ([`scripts/bundle-litellm.mjs:29-37`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/scripts/bundle-litellm.mjs#L29-L37), [`128-155`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/scripts/bundle-litellm.mjs#L128-L155)).
4. **OpenRouter Backstop Catalog:** Fetched from `https://openrouter.ai/api/v1/models` as a resale backstop ([`scripts/bundle-litellm.mjs:157-173`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/scripts/bundle-litellm.mjs#L157-L173)).

Output artifacts generated at build time:
- `src/data/litellm-snapshot.json` ([`src/models.ts:6`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L6)): Primary exact/canonical/prefix catalog.
- `src/data/pricing-fallback.json` ([`src/models.ts:7`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L7), [`152-162`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L152-L162)): Last-resort fallback so reseller keys never shadow canonical models.

### 3.2 Runtime Loading and Live Cache
- **Runtime Load (`loadPricing`)** ([`src/models.ts:305-327`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L305-L327)):
  - Checks on-disk cached pricing at `~/.cache/codeburn/litellm-pricing.json` (`getCachePath()`, [`src/models.ts:202-204`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L202-L204)).
  - Validates `CACHE_SCHEMA_VERSION === 3` and 24-hour TTL (`CACHE_TTL_MS = 86,400,000`) ([`src/models.ts:66-74`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L66-L74), [`278-289`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L278-L289)).
  - If missing/expired, fetches fresh LiteLLM rates over HTTPS with timeout (`fetchAndCachePricing()`, [`src/models.ts:245-276`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L245-L276)).
  - Merges bundled snapshot fallbacks over fetched data (`mergeSnapshotFallbacks`, [`src/models.ts:291-296`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L291-L296)).
  - Offline/Test mode bypass: `process.env['CODEBURN_PRICING_SNAPSHOT_ONLY']` skips network calls ([`src/models.ts:315-319`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L315-L319)).
- **Input Sanitization (`safePerTokenRate`)** ([`src/models.ts:206-216`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L206-L216)): Rejects negative rates, `NaN`, and `Infinity`, capping maximum rates at $1.00/token to prevent malicious/corrupt upstream inflation.

### 3.3 Model Resolution and Lookup Hierarchy
When `getModelCosts(model)` is called ([`src/models.ts:987-1057`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L987-L1057)), it evaluates in strict precedence:
1. **User Exact Price Overrides** (`userPriceOverrides`, [`src/models.ts:530-551`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L530-L551), [`993-994`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L993-L994)).
2. **Explicit User & Built-in Aliases** (`resolveAlias`, `BUILTIN_ALIASES`, [`src/models.ts:365-509`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L365-L509), [`847-853`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L847-L853), [`996-1003`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L996-L1003)).
3. **Exact Cache Matches** (`pricingCache.get(withPrefix)` / `pricingCache.get(canonical)`, [`src/models.ts:1005-1007`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L1005-L1007)).
4. **Router Prefix Peeling Candidates** (`routedModelCandidates`, [`src/models.ts:949-975`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L949-L975)): Peels `omniroute:`, `cp/`, `cline-pass/`, `cline-free/`, `cmd/`, `antigravity/`, `orcarouter/` ([`src/models.ts:936-947`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L936-L947), [`1009-1017`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L1009-L1017)).
5. **Prefix Overrides** (`getPriceOverridePrefix`, [`src/models.ts:579-586`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L579-L586), [`1019-1020`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L1019-L1020)).
6. **Longest-Prefix Match** (`getSortedPricingKeys`, [`src/models.ts:168-173`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L168-L173), [`1025-1029`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L1025-L1029)): Ensures `gpt-5-mini` matches `gpt-5-mini` rather than collapsing into `gpt-5`.
7. **Case-Insensitive User Overrides & Gap-Fill Index** (`getLowercasePricingIndex`, [`src/models.ts:185-200`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L185-L200), [`1031-1042`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L1031-L1042)).
8. **Variant Suffix Peeling** (`stripKnownPricingVariantSuffix`, [`src/models.ts:977-985`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L977-L985), [`1044-1055`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L1044-L1055)): Strips `:thinking`, `:cloud`, `-TEE`.

### 3.4 House Model Overrides, Flat-Rate SKUs, and Local Models
- **House Model Overrides (`BUILTIN_PRICE_OVERRIDES`)** ([`src/models.ts:84-89`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L84-L89)): Cursor Composer models (`composer-2.5`, `composer-2`, `composer-1.5`, `composer-1`) priced directly from published Cursor docs.
- **Flat-Rate / Subscription Models (`isFlatRateModel`)** ([`src/models.ts:660-756`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L660-L756)): Returns `$0` for Warp `auto`, Cline Pass `auto-genius`, Kimi `kimi-for-coding-highspeed`, `grok-composer-*`, `warp-auto-*`, preventing artificial spend creation.
- **Local Model Savings Accounting** ([`src/models.ts:597-643`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L597-L643), [`src/parser.ts:1187-1211`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/parser.ts#L1187-L1211)): Sets actual `costUSD = 0` for local inference models (e.g. Ollama, LM Studio) while calculating counterfactual `savingsUSD` against a user-configured baseline cloud model.
- **Subscription Proxied Paths (`isProxiedPath`)** ([`src/models.ts:795-836`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L795-L836)): Identifies project checkouts routed through subscription proxies.

---

## 4. Cost Engine: Gross vs. Net Costs and Calculation Logic

### 4.1 Cost Calculation Formula
All cost calculations flow through `calculateCost()` in [`src/models.ts:1184-1230`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L1184-L1230):
$$\text{Cost} = \text{Multiplier} \times \left( C_{\text{in}} + C_{\text{out}} + C_{\text{write,5m}} + C_{\text{write,1h}} + C_{\text{read}} + C_{\text{search}} \right)$$

Where:
- $C_{\text{in}} = \max(0, \text{inputTokens}) \times \text{inputCostPerToken}$
- $C_{\text{out}} = \max(0, \text{outputTokens}) \times \text{outputCostPerToken}$
- $C_{\text{write,5m}} = \text{safeFiveMinuteCacheCreation} \times \text{cacheWriteCostPerToken}$
- $C_{\text{write,1h}} = \text{safeOneHourCacheCreation} \times \text{cacheWriteCostPerToken} \times 1.6$  
  (`ONE_HOUR_CACHE_WRITE_MULTIPLIER_FROM_FIVE_MINUTE_RATE = 1.6`, [`src/models.ts:76`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L76), [`1226`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L1226))
- $C_{\text{read}} = \max(0, \text{cacheReadTokens}) \times \text{cacheReadCostPerToken}$
- $C_{\text{search}} = \max(0, \text{webSearchRequests}) \times \$0.01$ (`WEB_SEARCH_COST = 0.01`, [`src/models.ts:75`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L75), [`1228`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L1228))
- $\text{Multiplier} = \text{speed} == \text{'fast'} \ ? \ \text{fastMultiplier} : 1.0$ ([`src/models.ts:1216`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L1216))

### 4.2 Cache Rate Heuristics and Explicit Flags
When upstream pricing JSON omits explicit cache pricing, `buildCosts` establishes fallback rates ([`src/models.ts:95-111`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L95-L111)):
- **Cache Write Default:** $1.25 \times \text{inputCostPerToken}$ (Anthropic standard).
- **Cache Read Default:** $0.10 \times \text{inputCostPerToken}$ (90% prompt caching discount).
- **Explicit Flag (`cacheWriteCostIsExplicit`):** Tracks whether the rate was explicitly present or fabricated, preventing invalid cache write surcharges on providers that do not charge extra for writes ([`src/models.ts:17-25`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L17-L25), [`109`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L109), [`src/providers/codex.ts:1211-1214`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/codex.ts#L1211-L1214)).

### 4.3 Dynamic Prompt Volume Tiering
- **Grok 4.6 Tiered Rates (`tieredCostsFor`)** ([`src/models.ts:116-129`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L116-L129)):
  - Evaluates prompt volume: $\text{promptTokens} = \text{inputTokens} + \text{cacheReadTokens}$.
  - At $\ge 200,000$ prompt tokens (`GROK_4_6_PROMPT_TOKEN_THRESHOLD`), swaps base rates to high-tier rates: `$4.00/MTok` input, `$12.00/MTok` output, `$1.00/MTok` cache read (`GROK_4_6_HIGH_PROMPT_COSTS`, [`src/models.ts:117`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/models.ts#L117)).

### 4.4 Gross vs. Net Optimization Accounting
In the context optimization and savings engine (`src/optimize.ts`):
- **Effective Input Tokens / Gross Baseline** ([`src/optimize.ts:78-83`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/optimize.ts#L78-L83), [`1431`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/optimize.ts#L1431), [`1671`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/optimize.ts#L1671)):
  $$\text{effectiveInputTokens} = (\text{cacheWriteTokens} \times 1.25) + (\text{cacheReadTokens} \times 0.10)$$
  Used to estimate prompt bloat, MCP tool schema overhead, and repeat-turn context cost reductions.

---

## 5. Fallback Heuristics for Missing or Omitted Token Counts

When provider logs do not provide native token counts, Codeburn uses standardized fallback heuristics:

1. **Character Counting Rule (`estimateTokensFromChars`)** ([`src/token-estimate.ts:1-5`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/token-estimate.ts#L1-L5)):
   - Constant: `CHARS_PER_TOKEN = 4`.
   - Formula: $\lceil \text{characters} / 4 \rceil$.
2. **Metadata Transparency (`costIsEstimated`)** ([`src/types.ts:139-142`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/types.ts#L139-L142), [`src/providers/types.ts:42`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/types.ts#L42)):
   - Every call priced via estimated tokens sets `costIsEstimated: true` / `isEstimated: true`. Aggregates roll this up into `estimatedCostUSD` without altering total spend.
3. **Provider-Specific Estimations**:
   - **Codex:** Estimates from `pendingUserMessage.length` and `pendingOutputChars` when `last_token_usage` and `total_token_usage` are both absent ([`src/providers/codex.ts:1091-1115`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/codex.ts#L1091-L1115)).
   - **Cursor:** Cursor v3 SQLite bubble rows with 0 tokens fall back to `text_length` or `(userChars + contextChars)` and `assistantChars` ([`src/providers/cursor.ts:806-819`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/cursor.ts#L806-L819), [`887-890`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/cursor.ts#L887-L890), [`920-921`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/cursor.ts#L920-L921), [`src/providers/cursor-agent.ts:453-455`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/cursor-agent.ts#L453-L455)).
   - **Copilot:** Re-estimates missing assistant output tokens from `replyText` ([`src/providers/copilot.ts:1701-1702`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/copilot.ts#L1701-L1702)). Supports credit tracking where $10^9\text{ nano-AIU} = 1\text{ credit} = \$0.01$ ([`src/types.ts:169`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/types.ts#L169), [`src/providers/copilot.ts:74-78`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/copilot.ts#L74-L78)).
   - **Kiro:** Metered execution credits ($1\text{ credit} = \$0.04$) take precedence; falls back to char estimation if credits equal 0 ([`src/providers/kiro.ts:18`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/kiro.ts#L18), [`240-259`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/kiro.ts#L240-L259), [`387-408`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/kiro.ts#L387-L408)).
   - **Warp / QuickDesk:** Estimated from shell prompt source and message character lengths ([`src/providers/warp.ts:201`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/warp.ts#L201), [`405-406`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/warp.ts#L405-L406), [`src/providers/quickdesk.ts:499-500`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/quickdesk.ts#L499-L500)).
   - **Droid:** Splits session turn token counts evenly across all assistant calls within the turn, assigning the arithmetic remainder to the last call ([`src/providers/droid.ts:230-254`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/droid.ts#L230-L254)).
   - **Hermes:** Supports a three-tier cost basis (`actual` $\rightarrow$ `estimated` $\rightarrow$ `calculated`) based on database column availability ([`src/providers/hermes.ts:453-474`](file:///Users/robin.a.paul/Proj/token-analyzer/repositories/codeburn/src/providers/hermes.ts#L453-L474)).

---

## 6. Resolution Summary for GitHub Issue #62

1. **Token Calculation & Cache Reads/Writes:** `codeburn` normalizes provider-specific token events to Anthropic semantics (uncached input vs. cached read vs. cache write). Reasoning tokens are guarded by `REASONING_INCLUDED_IN_OUTPUT` (`claude`, `codex`, `copilot`) to prevent double-counting.
2. **Pricing Catalogs & Overrides:** Catalogs are structured into primary snapshots (`litellm-snapshot.json`) and fallback maps (`pricing-fallback.json`), refreshed at runtime with 24-hour disk caching. Supports user price overrides, user/built-in aliases, router prefix stripping, longest-prefix matching, case-insensitive indexing, and flat-rate SKU suppression.
3. **Gross vs. Net Cost Engine:** `calculateCost()` calculates net costs using tiered rates, ephemeral 1-hour cache write penalties ($1.6\times$), 5-minute cache writes ($1.25\times$), prompt cache read discounts ($0.10\times$), fast speed multipliers, and web search fees ($0.01$). Counterfactual local model savings calculate gross baseline costs against cloud models.
4. **Fallback Heuristics:** Employs `estimateTokensFromChars` ($\lceil\text{chars}/4\rceil$) and credit conversions (Kiro $0.04/credit, Copilot 1e9 nano-AIU = $0.01) with `costIsEstimated: true` flags when provider logs lack raw token counts.
