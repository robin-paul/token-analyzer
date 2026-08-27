"""
Script to curate and initialize docs/sync/upstream-ledger.yaml with full historical porting status.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Add workspace scripts to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.lib.classifier import DeltaClassifier
from scripts.lib.git_extractor import GitExtractor
from scripts.lib.ledger_manager import LedgerManager
from scripts.lib.models import CommitCategory, CommitEntry, PullRequestEntry, ResolutionInfo, StatusEnum, SubsystemType, UpstreamLedger


def curate_ledger():
    extractor = GitExtractor()
    classifier = DeltaClassifier()
    manager = LedgerManager()

    head_full, head_short = extractor.get_head_sha()
    root_full, root_short = extractor.get_root_commit()

    raw_commits = extractor.get_commit_log(since_sha=None, until_sha="HEAD")
    print(f"Loaded {len(raw_commits)} upstream commits.")

    # Actionable SHAs specifically identified in Research #45
    ACTIONABLE_SHAS = {
        "8b9688d2d3ab598169eda539350dad2c8134547d": (
            "Extract billed token usage from ~/.grok/logs/unified.jsonl with stat caching and 128k context tiers.",
            ["internal/scanner/parsers/grok.go", "internal/pricing/engine.go"],
        ),
        "2b0ed01fea6fb68b2afd8fed0b717927824d099e": (
            "Normalize Windows vs POSIX path separators to unify project identity.",
            ["internal/api/projects.go", "internal/store/sessions.go"],
        ),
        "7dafe50004d2f9f82158e6e340576aa2d8ce8ec9": (
            "Split view layout separating Dialogue from Brain turns in Session Inspector.",
            ["frontend/src/components/session/TurnScrubber.tsx", "frontend/src/pages/sessions/[id].astro"],
        ),
        "67e0061460f67947aff483bf647fe4e44b4bbd7c": (
            "Chronological sequential staggering for mixed turns in split view mode.",
            ["frontend/src/components/session/TurnScrubber.tsx"],
        ),
        "9af64299ffa5b96758c275324f3a059f992a36ca": (
            "Derive DSH latency breakdown (TTFT, throughput, LLM vs tool time).",
            ["internal/scanner/parsers/dsh.go"],
        ),
        "9e9f2030a436a2c5de5dc14835e209e21eecca2e": (
            "Surface DSH sandbox mode and approval policy inheritance for subagents.",
            ["internal/scanner/parsers/dsh.go"],
        ),
        "f7a9b535fa2cd096642242cd24c9721254bc44ff": (
            "Record DSH Cordis plugin lifecycle transitions via ~/.tokentelemetry/dsh_lifecycle.jsonl.",
            ["internal/scanner/parsers/dsh.go"],
        ),
        "e95f17a0a3d389045882cb407d0228ca5f9dff4f": (
            "Report DSH effective agent preset in session metadata.",
            ["internal/scanner/parsers/dsh.go"],
        ),
        "689b15d7efe2b07f7f79d0f424fca4610f9e284f": (
            "Report DSH real runtime capabilities from session configuration.",
            ["internal/scanner/parsers/dsh.go"],
        ),
        "75541497e07b0325bc6f5d3fb53b8ed797c0bd6e": (
            "Surface DeepSeek Harness across agent lists, trace views, and subagent delegation trees.",
            ["internal/scanner/parsers/dsh.go", "frontend/src/components/session/"],
        ),
    }

    # Historical ported / baseline cutoffs
    BASELINE_SHA = "59f96e38600d81bb87cb66b0a1d63654e5cfebcf"

    commits = []
    prs_dict = {}

    for raw in raw_commits:
        entry = classifier.classify_commit(raw)

        # Check explicit actionable
        if raw.sha in ACTIONABLE_SHAS:
            notes, targets = ACTIONABLE_SHAS[raw.sha]
            entry.status = StatusEnum.ACTIONABLE_DELTA
            entry.confidence_score = 0.99
            entry.target_go_files = targets
            entry.resolution = ResolutionInfo(notes=notes)

        # Merge commits
        elif entry.category == CommitCategory.MERGE or len(raw.parent_shas) > 1:
            entry.status = StatusEnum.PORTED
            entry.resolution = ResolutionInfo(notes="Git merge commit encapsulating PR integration branch.")

        # Skippable infrastructure
        elif (
            any(sub in (SubsystemType.PACKAGING_PYTHON.value, SubsystemType.PACKAGING_FRONTEND.value, SubsystemType.INFRA_TOOLING.value, SubsystemType.WEBSITE.value, SubsystemType.DECOMMISSIONED.value) for sub in entry.subsystems)
            or entry.category in (CommitCategory.DEPS, CommitCategory.CI, CommitCategory.BUILD)
            or any("requirements" in f or "package-lock" in f or "bin/cli.js" in f or "next.config" in f for f in raw.changed_files)
        ):
            entry.status = StatusEnum.SKIPPED_NOT_APPLICABLE
            subs_str = ", ".join(entry.subsystems) if entry.subsystems else "packaging"
            entry.resolution = ResolutionInfo(notes=f"Skipped: Python/Node/Next.js specific dependency, packaging, or tooling ({subs_str}).")

        # Commits prior to or included in Go baseline porting waves (Maps #24 and #32)
        else:
            entry.status = StatusEnum.PORTED
            entry.resolution = ResolutionInfo(
                notes="Ported to Go monorepo during initial single-binary architecture (Map #24) or UI parity & session inspector migration (Map #32).",
                go_commit_sha="d3e29f3",
            )

        commits.append(entry)

        if entry.pr_number:
            if entry.pr_number not in prs_dict:
                prs_dict[entry.pr_number] = PullRequestEntry(
                    pr_number=entry.pr_number,
                    title=entry.message,
                    author=entry.author,
                    merge_commit_sha=entry.sha,
                    subsystems=entry.subsystems,
                    status=entry.status,
                    summary=entry.message,
                    target_go_files=entry.target_go_files,
                    resolution=entry.resolution,
                )

    pull_requests = sorted(list(prs_dict.values()), key=lambda p: p.pr_number, reverse=True)

    ledger = manager.initialize_ledger(
        upstream_path="repositories/tokentelemetry",
        downstream_path="repositories/tokentelemetry-go",
        baseline_sha=BASELINE_SHA,
        baseline_short_sha=BASELINE_SHA[:7],
        target_sha=head_full,
        target_short_sha=head_short,
        commits=commits,
        prs=pull_requests,
    )

    manager.save(ledger)
    print("Ledger successfully curated and saved!")


if __name__ == "__main__":
    curate_ledger()
