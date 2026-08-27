# TokenTelemetry Upstream Parity & Delta Audit Report

**Generated:** `2026-08-27T01:48:30.149143+00:00`  
**Upstream Baseline:** `3806fc1`  
**Upstream HEAD:** `cecce1c`  
**Parity Percentage:** `27.4%`  

## 1. Synchronization Summary

- **Total Upstream Commits:** 426
- **Pull Requests:** 84
- **Ported to Go:** 100
- **Skipped (Non-Applicable):** 61
- **In Progress:** 0
- **Deferred:** 0
- **Actionable Deltas Pending:** 265

## 2. Actionable Pending Deltas

| Short SHA | Subsystem | Conventional Commit Message | Target Go Files |
| :--- | :--- | :--- | :--- |
| `489d593` | cli/collector | fix(cli): stamp the frontend install against the lockfile, not just package.json | `cmd/tt/` |
| `ead97fc` | frontend/analytics, frontend/core, frontend/inspector, frontend/projects | chore: clear frontend lint baseline | `frontend/src/`, `frontend/src/components/analytics/*`, `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/analytics/index.astro`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro` |
| `574a15d` | frontend/core | fix: update vulnerable frontend tooling | `frontend/src/` |
| `ca98efd` | cli/collector, docs, frontend/core, packaging/frontend | fix: harden local launcher defaults | `cmd/tt/`, `docs/`, `frontend/src/` |
| `3902247` | other | fix(deps): add zstandard to requirements.lock so DSH sessions scan | - |
| `67e0061` | frontend/inspector | feat(frontend): stagger mixed turns sequentially in split timeline mode | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `7dafe50` | frontend/inspector | feat(frontend): support sequential timeline flow in split view | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `a125dca` | frontend/inspector | fix(frontend): seek the playhead through the trace instead of truncating to it | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `ed40090` | frontend/inspector | fix(frontend): sync active step and scroll views on session playback scrubber seek | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `2b0ed01` | backend/api, backend/store, other | fix(backend): fold / vs \ separator variants into one project identity | `internal/api/projects.go`, `internal/api/router.go`, `internal/scanner/parsers/`, `internal/store/db.go`, `internal/store/sessions.go` |
| `8b9688d` | backend/api, frontend/inspector, other, pricing/engine | fix(grok): read billed usage from the unified inference log | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/pricing/engine.go`, `internal/pricing/pricing_data.json`, `internal/scanner/parsers/` |
| `59f96e3` | frontend/inspector | feat(frontend): add visual copy feedback for session ID in context panel | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `9af6429` | backend/api, frontend/inspector, other | feat: derive DSH latency breakdown (TTFT, throughput, LLM vs tool time) | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `9e9f203` | backend/api, frontend/inspector, other | feat: surface DSH sandbox mode and approval policy, incl. inherited by subagents | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `f7a9b53` | backend/api, docs, other | feat: record DSH plugin lifecycle transitions via a TT-authored plugin | `docs/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `e95f17a` | backend/api, frontend/inspector, other | fix: report DSH's effective agent preset, not just the header's | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `689b15d` | backend/api, frontend/inspector, other | fix: report DSH's real runtime capabilities, not another agent's config | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `7554149` | backend/api, frontend/core, frontend/inspector, other | fix: surface DeepSeek Harness across agent lists, trace, and delegation | `frontend/src/`, `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `f9f6a1f` | backend/api, frontend/core, other | feat: integrate DeepSeek Harness (dsh) as a supported agent | `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `4cc8e21` | frontend/inspector | feat(frontend): auto-scroll step index and execution timeline during replay and step jumping | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `084b6bd` | cli/collector | fix(cli): fall back to python -m venv if uv can't create it | `cmd/tt/` |
| `2dfd962` | other | docs: add UPDATE.json entry for the install fixes | - |
| `ddf29e6` | cli/collector, website | feat(cli): use uv for the backend bootstrap when it's already installed | `cmd/tt/` |
| `33d38b8` | cli/collector, website | fix(cli): repair a venv that has no pip instead of failing the install | `cmd/tt/` |
| `eb74d06` | frontend/inspector | fix(frontend): prevent aside layer shift and fix sticky header overlap | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `3336f9d` | other | docs: add UPDATE.json entry for the step index filter | - |
| `c451764` | frontend/inspector | fix(frontend): keep the step-index filter reachable and unclipped | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `866be30` | frontend/inspector | chore(merge): sync with origin/main and resolve conflicts in session detail view | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `41689a1` | frontend/inspector | feat(frontend): add step index category filter in session detail view | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `3d92521` | frontend/inspector | refactor(frontend): remove sticky top-[200px] from sidebars to fix layout height mismatch | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `286bc8d` | frontend/core, other | feat(hermes): keep explorer filters across a trip through the sidebar | `frontend/src/` |
| `618c0d0` | frontend/core, other | feat(hermes): replace explorer pagination with a load-more list | `frontend/src/` |
| `e2b3a3e` | pricing/engine | chore(pricing): refresh pricing_data.json from models.dev | `internal/pricing/engine.go`, `internal/pricing/pricing_data.json` |
| `42843d6` | website | chore(deps): bump the minor-and-patch group across 1 directory with 11 updates | - |
| `9ca4406` | frontend/core | chore(deps): bump the minor-and-patch group across 1 directory with 9 updates | `frontend/src/` |
| `2b5e914` | frontend/core, website | fix: update web apps for security audit | `frontend/src/` |
| `08c1c29` | backend/api, frontend/core, other | fix: stabilize rebased agent integrations | `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `60ce6cb` | website | feat: brand agent marquee icons | - |
| `7584c80` | website | fix: use current dashboard shot in showcase | - |
| `fa3d467` | website | feat: refresh website dashboard visuals | - |
| `831ec38` | frontend/core, website | fix: use Prime Agent brand color | `frontend/src/` |
| `7402e08` | frontend/analytics, frontend/core | fix: restore Pi branding across settings | `frontend/src/`, `frontend/src/components/analytics/*`, `frontend/src/pages/analytics/index.astro` |
| `2de617b` | frontend/core | feat: use branded Hermes mark on agent dashboard | `frontend/src/` |
| `c078b1c` | frontend/core, frontend/inspector, frontend/projects | fix: render agent brands and nested trace text | `frontend/src/`, `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro` |
| `7c95c56` | backend/api, frontend/core, frontend/inspector, other | fix: surface agent model and workspace metadata | `frontend/src/`, `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `265c437` | frontend/core, frontend/inspector | fix: render structured coding agent messages | `frontend/src/`, `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `5de560c` | backend/api, frontend/core, frontend/inspector, other | feat: ingest Muse and Prime agent sessions | `frontend/src/`, `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `fa775db` | docs, other | feat: integrate meta muse coding agent | `docs/` |
| `b6b940c` | backend/api, other | fix(billing): price Qwen and Cursor cache reads cumulatively | `internal/api/router.go`, `internal/scanner/parsers/` |
| `be2f218` | frontend/analytics, frontend/inspector | feat(analytics): disclose unpriced Claude activity | `frontend/src/components/analytics/*`, `frontend/src/components/session/*`, `frontend/src/pages/analytics/index.astro`, `frontend/src/pages/sessions/[id].astro` |
| `6e85da5` | backend/api, other | fix(claude): account for cumulative cache reads | `internal/api/router.go`, `internal/scanner/parsers/` |
| `87f5c56` | backend/api, frontend/core, other | fix: align Hermes explorer with current session schema | `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `dff2fd9` | frontend/inspector | fix(codex): collapse duplicate reasoning cards | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `8f75979` | frontend/inspector | fix(codex): normalize mirrored trace cards in UI | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `fdd35ec` | backend/api, other | fix(codex): collapse duplicate reasoning snapshots | `internal/api/router.go`, `internal/scanner/parsers/` |
| `59dd70d` | backend/api, other | fix(codex): remove mirrored trace projections | `internal/api/router.go`, `internal/scanner/parsers/` |
| `f071cb4` | frontend/core | feat: add Hermes session explorer UI | `frontend/src/` |
| `9a2d450` | backend/api, other | feat: add paginated Hermes session explorer API | `internal/api/router.go`, `internal/scanner/parsers/` |
| `4baddbe` | frontend/core, frontend/projects | feat: apply PR 245 scroll restoration | `frontend/src/`, `frontend/src/components/project/*`, `frontend/src/pages/projects/index.astro` |
| `c0db07c` | scanner/parsers | fix(security): dangerously skipping permissions in cli execution | `internal/scanner/parsers/` |
| `cae8315` | frontend/inspector | feat(frontend): add "Copied" confirmation state to session id copy button | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `d02914a` | backend/api, decommissioned, frontend/core, frontend/inspector, other | feat(hermes): honest telemetry for latency, cost provenance and outcomes | `frontend/src/`, `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `ac8372f` | backend/api, other | fix(gemini): restore chat-scan dedup and ghost-session guards | `internal/api/router.go`, `internal/scanner/parsers/` |
| `d93feef` | backend/api, other | fix(antigravity): prefer SQLite trace, fallback to transcript, and support jsonl chats | `internal/api/router.go`, `internal/scanner/parsers/` |
| `35bbd2b` | backend/api, other | refactor(antigravity): harden session trace + intent extraction | `internal/api/router.go`, `internal/scanner/parsers/` |
| `fcac1ab` | backend/api, frontend/inspector | fix(antigravity): fix session trace parser and display intent extraction | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `efb8b9f` | frontend/inspector | feat(frontend): sync step index scroll and inspector on dialogue card click | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `5ffc621` | pricing/engine | chore(pricing): refresh pricing_data.json from models.dev | `internal/pricing/engine.go`, `internal/pricing/pricing_data.json` |
| `a386ead` | pricing/engine | chore(pricing): refresh pricing_data.json from models.dev | `internal/pricing/engine.go`, `internal/pricing/pricing_data.json` |
| `0ebca00` | backend/api, other, website | fix(opencode): read channel-suffixed databases (opencode-<channel>.db) (#215) | `internal/api/router.go`, `internal/scanner/parsers/` |
| `06c733d` | backend/api, docs, frontend/inspector, frontend/projects, other | feat(goals): /goal telemetry for all four agents that ship it (#202) | `docs/`, `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `d1c2f37` | docs, frontend/core, frontend/projects | docs+fix: ban session URLs and machine identifiers; fix Windows project names (#213) | `docs/`, `frontend/src/`, `frontend/src/components/project/*`, `frontend/src/pages/projects/index.astro` |
| `36e5591` | docs, other, website | fix(container): forward TT_AUTH_TOKEN into the backend container (#200) | `docs/` |
| `965cc64` | docs, frontend/core, infra/tooling, other | feat: Docker/Podman compose support + GHCR CI (#172) | `docs/`, `frontend/src/` |
| `b0beeab` | backend/api, frontend/analytics, frontend/inspector, frontend/projects, other | fix(grok) + feat(loops): truthful loop cancellation & next-run time on active loops (#194) | `frontend/src/components/analytics/*`, `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/analytics/index.astro`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `e63ee72` | backend/api, frontend/projects, other, website | feat: artifact previews, Cards/List view toggle, docs screenshots | `frontend/src/components/project/*`, `frontend/src/pages/projects/index.astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `e890e8e` | frontend/projects | feat: show artifact count on the project Artifacts tab | `frontend/src/components/project/*`, `frontend/src/pages/projects/index.astro` |
| `a3ff2b6` | frontend/inspector, frontend/projects | fix: drop favicon emoji from artifact cards | `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro` |
| `de16fd7` | other | chore: drop backend/venv symlink accidentally committed | - |
| `0a73a94` | backend/api, frontend/inspector, frontend/projects, other | feat: surface Antigravity task/plan/walkthrough artifacts per project | `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `4915caf` | backend/api, backend/store, frontend/inspector, frontend/projects, other | feat: surface Claude Code published artifacts per project | `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/`, `internal/store/db.go`, `internal/store/sessions.go` |
| `5958d7b` | backend/api, other | fix(opencode): resolve the data dir across platforms/env, not just ~/.local/share (#179) | `internal/api/router.go`, `internal/scanner/parsers/` |
| `bb10a62` | backend/api, other, pricing/engine | fix(hermes): re-price sessions Hermes reports as $0.00 (custom/proxy endpoints) (#178) | `internal/api/router.go`, `internal/pricing/engine.go`, `internal/pricing/pricing_data.json`, `internal/scanner/parsers/` |
| `8aa3d43` | backend/api, frontend/inspector | perf(trace): speed up trace loading (mtime cache + O(n²)→O(n) pairing) (#186) | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `1f65c23` | pricing/engine | chore(pricing): refresh pricing_data.json from models.dev (#185) | `internal/pricing/engine.go`, `internal/pricing/pricing_data.json` |
| `b226fbe` | backend/api, frontend/inspector, other | feat(sessions): show model reasoning effort for every agent that records one (#183) | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `2eadf60` | frontend/core, frontend/inspector | fix: normalize Codex structured reasoning summaries before rendering (#181) (#182) | `frontend/src/`, `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `7fb578c` | backend/api, frontend/analytics, frontend/inspector, frontend/projects, other | feat(loops): project loop tabs + Grok & Cline detection (#177) | `frontend/src/components/analytics/*`, `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/analytics/index.astro`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `375f761` | backend/api, frontend/core, other | feat(settings): show each agent's experimental / feature flags (#175) | `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `a7548c7` | backend/api, backend/store, frontend/analytics, frontend/inspector, other | feat: /loop telemetry — detect, track & show recurring loops (re-land on main) (#169) | `frontend/src/components/analytics/*`, `frontend/src/components/session/*`, `frontend/src/pages/analytics/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/`, `internal/store/db.go`, `internal/store/sessions.go` |
| `ef3ec40` | frontend/analytics, frontend/core | fix(ui): label the total-tokens/cost scope on dashboard vs analytics (#168) | `frontend/src/`, `frontend/src/components/analytics/*`, `frontend/src/pages/analytics/index.astro` |
| `395b4e8` | backend/api, frontend/inspector, other | fix: attribute dynamic-workflow subagent tokens in Claude traces (#166) | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `f6927a0` | website | chore(deps): bump @types/node from 20.19.43 to 26.1.1 in /website (#158) | - |
| `6b43092` | website | chore(deps): bump framer-motion from 11.18.2 to 12.42.2 in /website (#155) | - |
| `7adf273` | frontend/core | chore(deps): bump @types/node from 20.19.43 to 26.1.1 in /frontend (#159) | `frontend/src/` |
| `422859b` | frontend/core | chore(deps): bump the minor-and-patch group in /frontend with 4 updates (#156) | `frontend/src/` |
| `34a50aa` | website | chore(deps): bump the minor-and-patch group in /website with 3 updates (#154) | - |
| `42e20e3` | other | fix(deps): regenerate requirements.lock as a universal cross-platform lock | - |
| `558f97f` | other | chore(deps): update pyyaml requirement in /backend | - |
| `700312b` | docs, other | docs: clarify how to relaunch/update; make installer self-update | `docs/` |
| `9a6d892` | cli/collector, frontend/core, infra/tooling, other, packaging/frontend, website | chore(deps): commit lockfiles, hash-pin backend, add dependabot | `cmd/tt/`, `frontend/src/` |
| `cd2fd76` | backend/api | fix(backend): redact auth token from uvicorn access logs | `internal/api/router.go`, `internal/scanner/parsers/` |
| `0892dce` | frontend/core, other | feat(hermes): two-profile diff view on the profiles page | `frontend/src/` |
| `181b8df` | backend/api, frontend/core, other | feat(hermes): profile scope UI, burn-rate budgets, kanban cost board | `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `70c2e72` | other | fix(tests): patch PI_SESSIONS_DIR in scan fixtures for hermeticity | - |
| `acbe753` | backend/api, frontend/core, frontend/inspector, other | feat(hermes): per-profile usage attribution and profiles dashboard | `frontend/src/`, `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `dc468f9` | pricing/engine | chore(pricing): refresh pricing_data.json from models.dev | `internal/pricing/engine.go`, `internal/pricing/pricing_data.json` |
| `f0bb039` | website | fix(website): derive ProofStrip agent count from data (was stale at 11) | - |
| `163c1da` | frontend/core | fix: use Pi's real brand mark + exact brand color for the pi agent | `frontend/src/` |
| `f8c64ec` | frontend/core | fix: recolor Pi agent from rose to fuchsia (#d946ef) | `frontend/src/` |
| `0e1df95` | backend/api, frontend/core, other | feat: add Pi Coding Agent session support (#135) | `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `c5aa74b` | other | docs: credit mariadb-KyleHutchinson in the release note for PR #131 | - |
| `e7e53eb` | backend/api, other | fix(copilot): stop double-counting cache tokens from CLI shutdown metrics | `internal/api/router.go`, `internal/scanner/parsers/` |
| `28a039d` | backend/api, other | fix(scan): version the sidecar cache, key freshness on subagent files too | `internal/api/router.go`, `internal/scanner/parsers/` |
| `fae935b` | docs, other | chore(audit): add /bug-audit skill with sonnet/opus subagent fleet | `docs/` |
| `b6da229` | other | docs: note full session-history coverage and accurate dating in UPDATE.json | - |
| `3323317` | backend/api, other | fix(claude): keep MCP-tool and Skill usage analytics on cache hits | `internal/api/router.go`, `internal/scanner/parsers/` |
| `33e6835` | backend/api, other | fix(scan): close codex stub-flip gap, harden cache paths, isolate test cache writes | `internal/api/router.go`, `internal/scanner/parsers/` |
| `d94b870` | backend/api, other | fix(codex): re-alias project from cached raw cwd on cache hits | `internal/api/router.go`, `internal/scanner/parsers/` |
| `305fdf7` | backend/api, other | fix(codex): remove 100-session parse cap, cache unchanged rollouts | `internal/api/router.go`, `internal/scanner/parsers/` |
| `1d032e5` | backend/api, other | fix(claude): keep memory artifacts fresh on cache hits, tidy cache field consistency | `internal/api/router.go`, `internal/scanner/parsers/` |
| `0fc514f` | backend/api, other | fix(claude): remove 100-session parse cap, cache unchanged transcripts | `internal/api/router.go`, `internal/scanner/parsers/` |
| `4bfe5f8` | other | feat(scan): add mtime-keyed sidecar parse cache | - |
| `b070a1d` | backend/store, other | fix(history): guard upsert_sessions against stub rows crushing real data | `internal/store/db.go`, `internal/store/sessions.go` |
| `dbd691a` | backend/api, other | refactor(scan): seed transient stub flag on claude/codex sessions | `internal/api/router.go`, `internal/scanner/parsers/` |
| `2f4b658` | backend/api, other | fix(sessions): drop phantom Copilot chats, strip OpenCode context tags | `internal/api/router.go`, `internal/scanner/parsers/` |
| `9ff5f35` | frontend/inspector, other | feat(trace): show per-step token usage in session traces | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `300b6e3` | backend/api, other | feat(sessions): show the typed prompt for IDE-originated Claude sessions | `internal/api/router.go`, `internal/scanner/parsers/` |
| `6be756f` | backend/api | fix(claude): derive session timestamp from last real turn, not file mtime | `internal/api/router.go`, `internal/scanner/parsers/` |
| `8a45236` | backend/store | fix(history): persist cache_reads so stored sessions keep the true cache-hit rate | `internal/store/db.go`, `internal/store/sessions.go` |
| `c02be79` | backend/api | fix: compute cache_hit_pct from cumulative cache reads, not the per-session high-water mark | `internal/api/router.go`, `internal/scanner/parsers/` |
| `dd69ab0` | pricing/engine | chore(pricing): refresh pricing_data.json from models.dev | `internal/pricing/engine.go`, `internal/pricing/pricing_data.json` |
| `90f7ad0` | backend/api, frontend/core, other, website | feat(agents): add Cline and SmallCode session scanning | `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `127ff40` | pricing/engine | chore(pricing): refresh pricing_data.json from models.dev | `internal/pricing/engine.go`, `internal/pricing/pricing_data.json` |
| `9f678e6` | frontend/core | fix(budgets): persist budget deletion immediately | `frontend/src/` |
| `ad9f04b` | backend/api, frontend/projects | feat(projects): group git-worktree activity under the parent repo | `frontend/src/components/project/*`, `frontend/src/pages/projects/index.astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `e62bfe1` | docs, frontend/core, other | chore(telemetry): track budget feature usage via existing pipeline | `docs/`, `frontend/src/` |
| `4ac0831` | docs | chore(claude): add 'verify before reporting done' rule for data features | `docs/` |
| `fa1b548` | docs, other | docs: document budgets & alerts (README section + UPDATE.json entry) | `docs/` |
| `171d81c` | frontend/inspector | refactor(trace): move subagents list to top of context inspector | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `fdaa340` | frontend/projects | fix(insights): bucket heatmap days in local time; add cost to tooltip | `frontend/src/components/project/*`, `frontend/src/pages/projects/index.astro` |
| `14bc8e9` | pricing/engine | chore(pricing): refresh pricing_data.json from models.dev | `internal/pricing/engine.go`, `internal/pricing/pricing_data.json` |
| `67942e1` | website | fix(website): add mobile nav menu for Docs/Resources/Install | - |
| `c000822` | backend/api, frontend/inspector, other | feat(frontend): surface Antigravity session artifacts in the trace Artifacts tab | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `8c75d26` | website | feat(website): instrument GA4 events across all routes + SPA page_view | - |
| `44a0835` | docs, website | feat(website): documentation site (Fumadocs) + community resources page | `docs/` |
| `c733cd6` | pricing/engine | chore(pricing): refresh pricing_data.json from models.dev | `internal/pricing/engine.go`, `internal/pricing/pricing_data.json` |
| `fd6e2c4` | docs, other | docs: retarget telemetry design + proxy docs to Cloudflare Analytics Engine | `docs/` |
| `fe6ae45` | backend/api, docs, frontend/analytics, frontend/core, other, website | feat: anonymous product telemetry via Cloudflare Analytics Engine + website redesign | `docs/`, `frontend/src/`, `frontend/src/components/analytics/*`, `frontend/src/pages/analytics/index.astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `6c97bfe` | backend/api, backend/store, docs, frontend/analytics, frontend/core, other | feat: durable analytics history + date/range filters | `docs/`, `frontend/src/`, `frontend/src/components/analytics/*`, `frontend/src/pages/analytics/index.astro`, `internal/api/router.go`, `internal/scanner/parsers/`, `internal/store/db.go`, `internal/store/sessions.go` |
| `5abd88b` | pricing/engine | chore(pricing): refresh pricing_data.json from models.dev | `internal/pricing/engine.go`, `internal/pricing/pricing_data.json` |
| `40a44d8` | backend/api, frontend/core, other | feat: chip-aware local power default + drain-priority billing routes | `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `34d5402` | scanner/parsers | fix: launch summarizer CLIs by resolved path and feed claude prompt via stdin | `internal/scanner/parsers/` |
| `a868b19` | docs, frontend/core, infra/tooling, other, packaging/frontend, website | fix: remove vulnerable/unused deps so npm audit is clean (#91) | `docs/`, `frontend/src/` |
| `8b012d3` | cli/collector | fix: reinstall frontend deps when package.json changes (#92) | `cmd/tt/` |
| `b84bf28` | frontend/analytics, frontend/projects | fix: scroll ecosystem lists inside their cards instead of growing the page | `frontend/src/components/analytics/*`, `frontend/src/components/project/*`, `frontend/src/pages/analytics/index.astro`, `frontend/src/pages/projects/index.astro` |
| `5bbcca6` | backend/api, frontend/inspector, other | feat: nested subagent trace drill-in (slide-over viewer + round-trip nav) | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `1bbdc9e` | backend/api, other | feat: recover codex skill usage from SKILL.md read breadcrumbs | `internal/api/router.go`, `internal/scanner/parsers/` |
| `fbaa1ef` | backend/api, other | fix: Windows-safe sqlite URIs and utf-8 workspace reads | `internal/api/router.go`, `internal/scanner/parsers/` |
| `d8133d0` | backend/api, frontend/analytics, frontend/projects, other | feat: gemini/qwen skill + MCP extraction, agent labels on ecosystem rows | `frontend/src/components/analytics/*`, `frontend/src/components/project/*`, `frontend/src/pages/analytics/index.astro`, `frontend/src/pages/projects/index.astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `84f7732` | frontend/projects | feat: delegation & ecosystem section on project Insights, per agent | `frontend/src/components/project/*`, `frontend/src/pages/projects/index.astro` |
| `226960f` | backend/api, frontend/analytics, other | feat: cross-agent delegation analytics (by-agent breakdown + child attribution) | `frontend/src/components/analytics/*`, `frontend/src/pages/analytics/index.astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `9e67521` | backend/api, docs, frontend/inspector, other | feat: delegation linkage for Grok Build, Codex and Antigravity CLI | `docs/`, `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `8958f5f` | other | feat: announce delegation & ecosystem telemetry in the update feed | - |
| `beee5ba` | frontend/analytics, frontend/projects | feat: ecosystem analytics section + usage overlay on config inventory | `frontend/src/components/analytics/*`, `frontend/src/components/project/*`, `frontend/src/pages/analytics/index.astro`, `frontend/src/pages/projects/index.astro` |
| `3409970` | backend/api, docs, other | feat: per-session skill and MCP usage telemetry + ecosystem analytics | `docs/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `cd99522` | frontend/inspector | feat: show delegated work on session detail (subagent tokens + cost) | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `58ac707` | backend/api, docs, other | feat: track subagent spawns and delegated token usage per session (Phase 1) | `docs/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `5e95a8c` | backend/api, other, pricing/engine | Fix issues #86, #87, #88 | `internal/api/router.go`, `internal/pricing/engine.go`, `internal/pricing/pricing_data.json`, `internal/scanner/parsers/` |
| `8cd7faa` | cli/collector | fix(cli): quote venv/python path so spaces in the repo path don't break setup on Windows | `cmd/tt/` |
| `6aab12a` | backend/api, cli/collector, frontend/core, other | feat(remote): scan-to-connect QR + one-time token bootstrap | `cmd/tt/`, `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `c278cce` | backend/api, cli/collector, docs, frontend/core, frontend/inspector, frontend/projects, other, scanner/parsers | feat(remote): require an access token for remote dashboard access | `cmd/tt/`, `docs/`, `frontend/src/`, `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `982ca3e` | frontend/core | refactor: key WhatsNewBanner dismissal on release id, not commit SHA | `frontend/src/` |
| `b68a75a` | other | chore(claude): add protect-sensitive-files PreToolUse hook | - |
| `62a3398` | backend/api, frontend/inspector | fix(antigravity): render per-step trace for CLI (agy) sessions | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `55284c2` | backend/api, cli/collector, frontend/core, other | feat: opt-in remote/tailnet access via --host and --allowed-origins | `cmd/tt/`, `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `a35cc4b` | backend/api | fix: hermes session scanner silently drops every session | `internal/api/router.go`, `internal/scanner/parsers/` |
| `a9a61e5` | backend/api, frontend/core | feat: move local power configuration to dedicated page and update dashboard toggle | `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `be70721` | backend/api, backend/store, cli/collector, docs, other, scanner/parsers | feat: add cmd.exe quote tip and precise data-dir logging | `cmd/tt/`, `docs/`, `internal/api/projects.go`, `internal/api/router.go`, `internal/scanner/parsers/`, `internal/store/sessions.go` |
| `3f49a16` | backend/api, frontend/core, other | feat: Add CO2 footprint estimation for local models | `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `11b2dd6` | frontend/core, other | feat: add Local & Power insights surface | `frontend/src/` |
| `39cef53` | backend/api, other | feat: implement local energy insights and cloud savings | `internal/api/router.go`, `internal/scanner/parsers/` |
| `b9a53bd` | other | fix(power): harden battery parse, scheme-insensitive LAN match, cap costPerKwh | - |
| `e756b69` | backend/api, frontend/core, other | fix(power): decode unsigned battery amperage + bound/guard measured watts | `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `f958dbd` | other | docs: UPDATE.json entry for local-model power costing | - |
| `4c16446` | frontend/core | feat(power): Local power & electricity Settings UI + calibration | `frontend/src/` |
| `ac00fdc` | backend/api, other, pricing/engine | feat(power): endpoint/provider-based local detection + measured/model-aware tok/s | `internal/api/router.go`, `internal/pricing/engine.go`, `internal/pricing/pricing_data.json`, `internal/scanner/parsers/` |
| `edc29db` | other | feat(power): real hardware power measurement module (no-sudo, honest fallback) | - |
| `2aa1a9b` | backend/api, frontend/core, infra/tooling, other, pricing/engine | Cost & token accuracy overhaul (cache-write pricing, dynamic pricing, local/subscription cost, per-agent billing mode) (#74) | `frontend/src/`, `internal/api/router.go`, `internal/pricing/engine.go`, `internal/pricing/pricing_data.json`, `internal/scanner/parsers/` |
| `e4d9808` | other | chore: drop accidentally-committed worktree gitlinks and unrelated simulate.py | - |
| `cb2de5a` | backend/api, frontend/core, other | feat(cost): per-agent billing mode (API bill vs. subscription equivalent) | `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `7a00992` | backend/api, other, pricing/engine | feat: power & subscription cost config for local/subscription models | `internal/api/router.go`, `internal/pricing/engine.go`, `internal/pricing/pricing_data.json`, `internal/scanner/parsers/` |
| `74fa5c3` | frontend/core, other | feat(dashboard): show subscription cost disclaimer in full | `frontend/src/` |
| `ac9a140` | backend/api, other, pricing/engine | fix: price Anthropic prompt-cache writes at 1.25x input rate (#68) | `internal/api/router.go`, `internal/pricing/engine.go`, `internal/pricing/pricing_data.json`, `internal/scanner/parsers/` |
| `d739357` | infra/tooling, other, pricing/engine | feat(pricing): build-time pricing data from models.dev (no runtime network) | `internal/pricing/engine.go`, `internal/pricing/pricing_data.json` |
| `cf618b2` | backend/api, other | fix(antigravity): permanent project resolution + hide "unassigned" from Projects (#69) | `internal/api/router.go`, `internal/scanner/parsers/` |
| `960341b` | backend/api, docs, frontend/core, other, website | feat(privacy): disclose the update check + add in-app opt-out toggle (#64) (#67) | `docs/`, `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `10952c8` | backend/api, other | feat(antigravity): resolve real model + project for agy CLI sessions (#63) | `internal/api/router.go`, `internal/scanner/parsers/` |
| `2033870` | backend/api | fix: restrict /config project param to safe roots (#54) (#58) | `internal/api/router.go`, `internal/scanner/parsers/` |
| `1382c5a` | frontend/core, scanner/parsers | fix: pass prompts via stdin (#50) and retain summary on error (#51) (#62) | `frontend/src/`, `internal/scanner/parsers/` |
| `0d2010f` | frontend/core | fix: sanitize remote-sourced hrefs in WhatsChangedDrawer (#56) (#59) | `frontend/src/` |
| `df18613` | backend/api, frontend/core, other, scanner/parsers | fix: SQLite leak, cron validation, summarizer backend validation (#52, #53, #57) (#60) | `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `fa33e08` | backend/api, docs, frontend/core, other, scanner/parsers | feat(summarizer): add config-driven OpenAI-compatible backend (#48) | `docs/`, `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `bb9a173` | backend/api, frontend/analytics, frontend/core, frontend/inspector, frontend/projects | fix: use cache high-watermark for cost + relabel to 'API equiv.' (#42) (#46) | `frontend/src/`, `frontend/src/components/analytics/*`, `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/analytics/index.astro`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `12c2434` | backend/api, frontend/core, frontend/inspector, frontend/projects, other | feat(antigravity): surface sub-label + IDE coverage + dedup (#47) | `frontend/src/`, `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `a73fec5` | backend/api | feat: implement token usage estimation for Antigravity sessions (#40) | `internal/api/router.go`, `internal/scanner/parsers/` |
| `67a5e62` | backend/api, frontend/core, frontend/inspector, frontend/projects, other | feat(copilot): add Copilot CLI source + surface sub-label (#36) (#44) | `frontend/src/`, `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `2fa43e1` | backend/api, frontend/inspector | fix(opencode): resolve session-level + mixed models (#39) (#43) | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `31321f0` | backend/api | fix: extract modelID directly from OpenCode DB messages (#41) | `internal/api/router.go`, `internal/scanner/parsers/` |
| `3aa3607` | backend/api, frontend/core, frontend/projects, other | feat: per-project token budgets + notification center | `frontend/src/`, `frontend/src/components/project/*`, `frontend/src/pages/projects/index.astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `f00dfb5` | backend/api, docs, frontend/core, frontend/inspector, frontend/projects, other, pricing/engine, website | Grok Build (xAI) support + Copilot & back-nav fixes (#37) | `docs/`, `frontend/src/`, `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/pricing/engine.go`, `internal/pricing/pricing_data.json`, `internal/scanner/parsers/` |
| `4b20aeb` | docs, other | chore(claude): enforce UPDATE.json on feat: pushes via PreToolUse hook (#35) | `docs/` |
| `5830ab6` | backend/api | fix(update-check): reject cache entries with non-SHA `latest` (#34) | `internal/api/router.go`, `internal/scanner/parsers/` |
| `1544c6a` | docs, other | chore(claude): enforce UPDATE.json on feat: pushes via PreToolUse hook | `docs/` |
| `0f22ef7` | backend/api, cli/collector, frontend/analytics, frontend/core, frontend/inspector, other, scanner/parsers | Summarizer, schedules read-only, update banner, port config + fixes (#33) | `cmd/tt/`, `frontend/src/`, `frontend/src/components/analytics/*`, `frontend/src/components/session/*`, `frontend/src/pages/analytics/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `06bceca` | website | Website analytics + consent, cost-accounting & parser fixes (#32) | - |
| `d586807` | backend/api, cli/collector, frontend/analytics, frontend/core, frontend/inspector, other, pricing/engine | Audit fixes: token accounting, Windows safety, analytics filter (#29) | `cmd/tt/`, `frontend/src/`, `frontend/src/components/analytics/*`, `frontend/src/components/session/*`, `frontend/src/pages/analytics/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/pricing/engine.go`, `internal/pricing/pricing_data.json`, `internal/scanner/parsers/` |
| `95f55d7` | docs, frontend/core | feat(feedback): in-app feedback button + Discussions surfaces | `docs/`, `frontend/src/` |
| `1d416b6` | infra/tooling, other | chore(traffic): move sheet id to TT_SHEET_ID secret | - |
| `7d93580` | infra/tooling, other | feat(traffic): weekly GitHub traffic sync to Google Sheets | - |
| `3176d40` | frontend/inspector | fix(hermes-trace): dedupe React key in per-call breakdown | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `1e79f7c` | website | fix(og): surface Hermes Agent in the link-preview card | - |
| `5503c4c` | other | fix(scripts): publish-plugin.sh — brace var, copy correct paths | - |
| `2c23050` | docs, other, website | feat(hermes): prep standalone plugin repo + multi-agent empty state | `docs/` |
| `80f12d1` | docs, other | feat(hermes): add Hermes Dashboard plugin (launcher for TokenTelemetry) | `docs/` |
| `4e94325` | backend/api, docs, frontend/core | fix(hermes): honor HERMES_HOME env var instead of hardcoding ~/.hermes | `docs/`, `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `0873b9f` | frontend/analytics, frontend/core, frontend/projects | feat(format): centralise token + cost formatters, add B/T suffixes | `frontend/src/`, `frontend/src/components/analytics/*`, `frontend/src/components/project/*`, `frontend/src/pages/analytics/index.astro`, `frontend/src/pages/projects/index.astro` |
| `f839b73` | backend/api | chore(hermes): drop demo-mode session injection from production | `internal/api/router.go`, `internal/scanner/parsers/` |
| `3432aa8` | backend/api, docs, frontend/core, frontend/inspector, website | feat(hermes): dedicated /hermes dashboard + 38 source platforms + marketing | `docs/`, `frontend/src/`, `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `dd97cd3` | backend/api, frontend/core, frontend/inspector, pricing/engine, website | feat(hermes): add Hermes Agent support (#20) | `frontend/src/`, `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/pricing/engine.go`, `internal/pricing/pricing_data.json`, `internal/scanner/parsers/` |
| `416559f` | website | seo: ship favicon.ico + apple/PWA icons at site root | - |
| `5c6c77b` | docs, website | seo: register 'Token Telemetry' (spaced) as brand entity | `docs/` |
| `0524506` | website | fix: mobile responsiveness across marketing website | - |
| `f7b4ae0` | backend/api, docs, frontend/inspector, frontend/projects, website | feat: insights revamp, antigravity log-only traces, hero terminal replay | `docs/`, `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `5cc8927` | website | feat(website): redesign marketing site to match new app design system | - |
| `ae5632a` | website | chore(website): collapse sidebar in analytics screenshot | - |
| `bc2bf18` | website | chore(website): re-capture analytics with chart fully drawn | - |
| `8b06046` | frontend/core, website | chore(website): tighter screenshots — collapsed sidebar + trimmed canvas | `frontend/src/` |
| `991c27b` | frontend/inspector, website | chore(website): refresh marketing screenshots for new UI | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `e2251a7` | frontend/analytics, frontend/core, frontend/inspector, frontend/projects | feat: revamp UI/UX with token-driven design system + theme toggle | `frontend/src/`, `frontend/src/components/analytics/*`, `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/analytics/index.astro`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro` |
| `3d7c030` | frontend/core | chore: remove quality signals section and related components | `frontend/src/` |
| `0d260d7` | frontend/core | chore: comment out cache hit % card on dashboard | `frontend/src/` |
| `3bb4001` | backend/api, frontend/core | Revert "feat: uncomment quality signals on dashboard frontend and backend" | `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `de58112` | backend/api, frontend/core | feat: uncomment quality signals on dashboard frontend and backend | `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `5657366` | backend/api, frontend/core, frontend/inspector, other, website | feat: antigravity log-only sessions, dedup fixes, comment out quality signals | `frontend/src/`, `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `cdbc570` | backend/api, frontend/projects | feat(config): surface plugins as a 6th entity across coding agents | `frontend/src/components/project/*`, `frontend/src/pages/projects/index.astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `2d9042d` | website | seo: keyword-loaded H1, FAQ section + FAQPage schema, drop npm-soon line | - |
| `da753d2` | website | chore(website): serve llms.txt and install scripts from domain | - |
| `f3a1977` | docs | Update model version in README | `docs/` |
| `0fc8d09` | docs | Update model analytics comparison in README | `docs/` |
| `b89ebbb` | docs | fix: remove npm (not available), add correct install.sh and install.ps1 URLs | `docs/` |
| `74dc985` | other | docs: add CITATION.cff for software citation | - |
| `0476922` | other | chore: add MIT LICENSE file | - |
| `1ec6ebb` | website | feat(seo): add Bing Webmaster verification meta tag | - |
| `94f8e3c` | website | fix(seo): tighten post-build regex to not corrupt RSC payload | - |
| `0c29f6b` | website | feat(seo): metadata, OG image, robots, sitemap, JSON-LD | - |
| `72a8a66` | website | fix(website): mobile-responsive Hero + 'AI agents' -> 'coding agents' | - |
| `3e84a89` | frontend/core, frontend/projects, website | feat: TokenTelemetry rebrand polish + landing site | `frontend/src/`, `frontend/src/components/project/*`, `frontend/src/pages/projects/index.astro` |
| `fd76725` | other | fix(install): point installer at tokentelemetry repo + add Windows PowerShell installer | - |
| `5d2eada` | backend/api, cli/collector, docs, frontend/core, other, packaging/frontend | Rename project: agent-harness -> tokentelemetry | `cmd/tt/`, `docs/`, `frontend/src/`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `6991b27` | frontend/inspector | Use 127.0.0.1 instead of localhost in session detail fetches (Windows compat) | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `5f87e77` | frontend/inspector | Revert session trace UI to pre-Windows-merge layout | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro` |
| `39d2cfe` | backend/api, frontend/inspector, other | Ignore graphify build artifacts; follow-on tweaks to backend and session trace | `frontend/src/components/session/*`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `9db558f` | backend/api, cli/collector, docs, frontend/analytics, frontend/core, frontend/inspector, frontend/projects | Fix Windows compatibility and enhance Claude/Codex trace rendering | `cmd/tt/`, `docs/`, `frontend/src/`, `frontend/src/components/analytics/*`, `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/analytics/index.astro`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/scanner/parsers/` |
| `f3772de` | backend/api, frontend/analytics, frontend/core, frontend/inspector, frontend/projects, pricing/engine | Add per-model cost pricing, fix reasoning trace UX, surface Antigravity artifacts | `frontend/src/`, `frontend/src/components/analytics/*`, `frontend/src/components/project/*`, `frontend/src/components/session/*`, `frontend/src/pages/analytics/index.astro`, `frontend/src/pages/projects/index.astro`, `frontend/src/pages/sessions/[id].astro`, `internal/api/router.go`, `internal/pricing/engine.go`, `internal/pricing/pricing_data.json`, `internal/scanner/parsers/` |