from __future__ import annotations
from typing import List, Dict, Any
from scripts.lib.models import StatusEnum, UpstreamLedger


class ReportGenerator:
    def __init__(self, ledger: UpstreamLedger):
        self.ledger = ledger

    def generate_parity_report(self) -> str:
        summary = self.ledger.summary
        report_lines = [
            "# TokenTelemetry Upstream Parity & Delta Audit Report",
            "",
            f"**Generated:** `{self.ledger.last_updated_at}`  ",
            f"**Upstream Baseline:** `{self.ledger.repository.baseline_short_sha}`  ",
            f"**Upstream HEAD:** `{self.ledger.repository.target_short_sha}`  ",
            f"**Parity Percentage:** `{summary.parity_percentage:.1f}%`  ",
            "",
            "## 1. Synchronization Summary",
            "",
            f"- **Total Upstream Commits:** {summary.total_commits}",
            f"- **Pull Requests:** {summary.total_pull_requests}",
            f"- **Ported to Go:** {summary.ported_count}",
            f"- **Skipped (Non-Applicable):** {summary.skipped_not_applicable_count}",
            f"- **In Progress:** {summary.in_progress_count}",
            f"- **Deferred:** {summary.deferred_count}",
            f"- **Actionable Deltas Pending:** {summary.actionable_delta_count}",
            "",
            "## 2. Actionable Pending Deltas",
            "",
        ]

        actionable = [c for c in self.ledger.commits if c.status == StatusEnum.ACTIONABLE_DELTA]
        if not actionable:
            report_lines.append("No actionable deltas pending. Downstream is in full functional parity with upstream.")
        else:
            report_lines.append("| Short SHA | Subsystem | Conventional Commit Message | Target Go Files |")
            report_lines.append("| :--- | :--- | :--- | :--- |")
            for c in actionable:
                subs = ", ".join(c.subsystems) if c.subsystems else "general"
                targets = ", ".join(f"`{t}`" for t in c.target_go_files) if c.target_go_files else "-"
                report_lines.append(f"| `{c.short_sha}` | {subs} | {c.message} | {targets} |")

        return "\n".join(report_lines)

    def generate_all_issue_specs(self) -> List[Dict[str, Any]]:
        actionable = [c for c in self.ledger.commits if c.status == StatusEnum.ACTIONABLE_DELTA]
        specs = []
        for c in actionable:
            title = f"Port Upstream [{c.short_sha}]: {c.message}"
            subs = ", ".join(c.subsystems) if c.subsystems else "general"
            targets = "\n".join(f"- `{t}`" for t in c.target_go_files) if c.target_go_files else "- None"
            notes = c.resolution.notes if c.resolution and c.resolution.notes else c.message

            body = f"""## Context & Upstream Delta

* **Upstream Commit:** `{c.sha}` (`{c.short_sha}`)
* **Author:** `{c.author}`
* **Date:** `{c.date}`
* **Subsystems:** `{subs}`
* **Upstream Message:** `{c.message}`

## Specification & Porting Requirements

{notes}

## Target Go Files

{targets}

## Acceptance Criteria

1. **Functional Parity:** Implement equivalent logic in `repositories/tokentelemetry-go` adhering to `CONTEXT.md` domain vocabulary.
2. **Unit / Integration Tests:** Add comprehensive Go unit tests verifying edge cases and error handling (`go test -v -race ./...`).
3. **Sync Ledger Update:** Update `docs/sync/upstream-ledger.yaml` using `uv run scripts/upstream-sync.py triage {c.short_sha} --status ported --go-commit <sha>`.
"""
            specs.append({
                "short_sha": c.short_sha,
                "title": title,
                "body": body,
            })
        return specs
