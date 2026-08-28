from __future__ import annotations
import datetime
from pathlib import Path
from typing import List, Optional
import yaml
from scripts.lib.models import (
    CommitEntry,
    PullRequestEntry,
    RepositoryInfo,
    ResolutionInfo,
    StatusEnum,
    SummaryInfo,
    UpstreamLedger,
)


class LedgerManager:
    def __init__(self, ledger_path: str = "docs/sync/upstream-ledger.yaml"):
        self.ledger_path = Path(ledger_path)

    def exists(self) -> bool:
        return self.ledger_path.exists()

    def load(self) -> UpstreamLedger:
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return UpstreamLedger.model_validate(data)

    def recompute_summary(self, ledger: UpstreamLedger) -> SummaryInfo:
        total = len(ledger.commits)
        actionable = sum(1 for c in ledger.commits if c.status == StatusEnum.ACTIONABLE_DELTA)
        ported = sum(1 for c in ledger.commits if c.status == StatusEnum.PORTED)
        in_progress = sum(1 for c in ledger.commits if c.status == StatusEnum.IN_PROGRESS)
        deferred = sum(1 for c in ledger.commits if c.status == StatusEnum.DEFERRED)
        skipped = sum(1 for c in ledger.commits if c.status == StatusEnum.SKIPPED_NOT_APPLICABLE)
        resolved = ported + skipped
        parity = (resolved / max(1, total)) * 100.0

        return SummaryInfo(
            total_commits=total,
            total_pull_requests=len(ledger.pull_requests),
            actionable_delta_count=actionable,
            ported_count=ported,
            in_progress_count=in_progress,
            deferred_count=deferred,
            skipped_not_applicable_count=skipped,
            un_triaged_count=0,
            parity_percentage=round(parity, 1),
        )

    def save(self, ledger: UpstreamLedger) -> None:
        import json
        ledger.summary = self.recompute_summary(ledger)
        ledger.last_updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        raw_dict = json.loads(ledger.model_dump_json(exclude_none=True))
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write("# yaml-language-server: $schema=./upstream-ledger.schema.json\n")
            yaml.dump(raw_dict, f, sort_keys=False, default_flow_style=False, allow_unicode=True)

    def update_commit_triage(
        self,
        sha_prefix: str,
        status: StatusEnum,
        notes: Optional[str] = None,
        go_commit_sha: Optional[str] = None,
        go_pr_number: Optional[int] = None,
        github_issue_id: Optional[int] = None,
    ) -> CommitEntry:
        ledger = self.load()
        matched: Optional[CommitEntry] = None
        for c in ledger.commits:
            if c.sha.startswith(sha_prefix) or c.short_sha.startswith(sha_prefix):
                matched = c
                break

        if not matched:
            raise ValueError(f"No commit found matching SHA prefix: '{sha_prefix}'")

        matched.status = status
        if not matched.resolution:
            matched.resolution = ResolutionInfo()

        if notes is not None:
            matched.resolution.notes = notes
        if go_commit_sha is not None:
            matched.resolution.go_commit_sha = go_commit_sha
        if go_pr_number is not None:
            matched.resolution.go_pr_number = go_pr_number
        if github_issue_id is not None:
            matched.resolution.github_issue_id = github_issue_id

        self.save(ledger)
        return matched

    def initialize_ledger(
        self,
        upstream_path: str,
        downstream_path: str,
        baseline_sha: str,
        baseline_short_sha: str,
        target_sha: str,
        target_short_sha: str,
        commits: List[CommitEntry],
        prs: List[PullRequestEntry],
    ) -> UpstreamLedger:
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        repo = RepositoryInfo(
            upstream_path=upstream_path,
            downstream_path=downstream_path,
            baseline_commit=baseline_sha,
            baseline_short_sha=baseline_short_sha,
            baseline_tag_or_label="initial-upstream-root",
            target_commit=target_sha,
            target_short_sha=target_short_sha,
        )
        ledger = UpstreamLedger(
            schema_version="1.0.0",
            generated_at=now_str,
            last_updated_at=now_str,
            repository=repo,
            summary=SummaryInfo(),
            pull_requests=prs,
            commits=commits,
        )
        ledger.summary = self.recompute_summary(ledger)
        return ledger
