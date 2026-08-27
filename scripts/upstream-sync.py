#!/usr/bin/env python3
"""
TokenTelemetry: Upstream Delta Tracking and Sync Ledger CLI Utility
Local-first, zero-network tool for auditing, triaging, and tracking upstream commits.
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# Add workspace scripts to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.lib.classifier import DeltaClassifier
from scripts.lib.git_extractor import GitExtractor
from scripts.lib.ledger_manager import LedgerManager
from scripts.lib.models import (
    CommitCategory,
    CommitEntry,
    PullRequestEntry,
    StatusEnum,
    SubsystemType,
    UpstreamLedger,
)
from scripts.lib.report_generator import ReportGenerator


def cmd_status(args: argparse.Namespace) -> int:
    manager = LedgerManager(args.ledger)
    if not manager.exists():
        print(
            f"Error: Sync ledger not found at {args.ledger}. Run `upstream-sync.py scan` first.",
            file=sys.stderr,
        )
        return 1

    ledger = manager.load()
    summary = ledger.summary

    if args.format == "json":
        print(json.dumps(summary.model_dump(), indent=2))
        return 0

    print("=" * 70)
    print("TokenTelemetry: Upstream Synchronization & Parity Status")
    print("=" * 70)
    print(f"Upstream Path:       {ledger.repository.upstream_path}")
    print(f"Downstream Path:     {ledger.repository.downstream_path}")
    print(
        f"Baseline Commit:     {ledger.repository.baseline_short_sha} ({ledger.repository.baseline_tag_or_label or 'root'})"
    )
    print(f"Target Commit (HEAD):{ledger.repository.target_short_sha}")
    print(f"Last Updated:        {ledger.last_updated_at}")
    print("-" * 70)
    print(f"Total Commits:       {summary.total_commits}")
    print(f"Pull Requests:       {summary.total_pull_requests}")
    print(
        f"Ported to Go:        {summary.ported_count} ({summary.ported_count / max(1, summary.total_commits) * 100:.1f}%)"
    )
    print(
        f"Skipped (Non-Applic):{summary.skipped_not_applicable_count} ({summary.skipped_not_applicable_count / max(1, summary.total_commits) * 100:.1f}%)"
    )
    print(f"In Progress:         {summary.in_progress_count}")
    print(f"Deferred:            {summary.deferred_count}")
    print(f"Actionable Deltas:   {summary.actionable_delta_count}")
    print("-" * 70)
    print(f"Parity Percentage:   {summary.parity_percentage:.1f}%")
    print("=" * 70)

    if summary.actionable_delta_count > 0:
        print("\nActionable Unported Deltas:")
        for c in ledger.commits:
            if c.status == StatusEnum.ACTIONABLE_DELTA:
                subs = ",".join(c.subsystems) if c.subsystems else "general"
                print(f"  • [{c.short_sha}] ({subs}) {c.message}")
    else:
        print("\nAll upstream commits are accounted for (100% parity).")

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    manager = LedgerManager(args.ledger)
    if not manager.exists():
        print(
            f"Error: Sync ledger not found at {args.ledger}. Run `upstream-sync.py scan` first.",
            file=sys.stderr,
        )
        return 1

    ledger = manager.load()
    commits = ledger.commits

    if args.status:
        status_filter = StatusEnum(args.status)
        commits = [c for c in commits if c.status == status_filter]

    if args.subsystem:
        commits = [c for c in commits if any(args.subsystem in s for s in c.subsystems)]

    if args.limit and args.limit > 0:
        commits = commits[: args.limit]

    if args.format == "json":
        print(json.dumps([c.model_dump() for c in commits], indent=2))
        return 0

    if args.format == "markdown":
        print("| SHA | Status | Subsystems | Message |")
        print("| :--- | :--- | :--- | :--- |")
        for c in commits:
            subs = "<br>".join(c.subsystems) if c.subsystems else "-"
            print(f"| `{c.short_sha}` | `{c.status.value}` | {subs} | {c.message} |")
        return 0

    # Default Table format
    print(f"{'SHA':<9} {'STATUS':<24} {'SUBSYSTEMS':<24} {'MESSAGE'}")
    print("-" * 90)
    for c in commits:
        subs = ",".join(c.subsystems) if c.subsystems else "-"
        if len(subs) > 23:
            subs = subs[:20] + "..."
        msg = c.message
        if len(msg) > 40:
            msg = msg[:37] + "..."
        print(f"{c.short_sha:<9} {c.status.value:<24} {subs:<24} {msg}")

    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    extractor = GitExtractor(args.upstream_path, args.downstream_path)
    manager = LedgerManager(args.ledger)

    sha = args.target
    matched_commit: Optional[CommitEntry] = None
    if manager.exists():
        ledger = manager.load()
        for c in ledger.commits:
            if c.sha.startswith(sha) or c.short_sha.startswith(sha):
                matched_commit = c
                sha = c.sha
                break

    try:
        diff_output = extractor.get_commit_diff(sha)
    except Exception as e:
        print(f"Error extracting diff for '{sha}': {e}", file=sys.stderr)
        return 1

    print("=" * 80)
    if matched_commit:
        print(f"Commit:        {matched_commit.sha} ({matched_commit.short_sha})")
        print(f"Author:        {matched_commit.author}")
        print(f"Date:          {matched_commit.date}")
        print(f"Subject:       {matched_commit.message}")
        print(f"Status:        {matched_commit.status.value}")
        print(f"Subsystems:    {', '.join(matched_commit.subsystems)}")
        if matched_commit.target_go_files:
            print(f"Target Go:     {', '.join(matched_commit.target_go_files)}")
    else:
        print(f"Commit SHA:    {sha}")
    print("=" * 80)
    print(diff_output)
    return 0


def cmd_triage(args: argparse.Namespace) -> int:
    manager = LedgerManager(args.ledger)
    if not manager.exists():
        print(f"Error: Sync ledger not found at {args.ledger}.", file=sys.stderr)
        return 1

    status = StatusEnum(args.status)
    try:
        updated = manager.update_commit_triage(
            sha_prefix=args.target,
            status=status,
            notes=args.notes,
            go_commit_sha=args.go_commit,
            go_pr_number=args.go_pr,
            github_issue_id=args.issue,
        )
        print(
            f"Successfully triaged commit [{updated.short_sha}] -> status='{updated.status.value}'"
        )
        if updated.resolution and updated.resolution.notes:
            print(f"  Notes: {updated.resolution.notes}")
        if updated.resolution and updated.resolution.go_commit_sha:
            print(f"  Go Commit: {updated.resolution.go_commit_sha}")
        return 0
    except Exception as e:
        print(f"Error updating triage state: {e}", file=sys.stderr)
        return 1


def cmd_scan(args: argparse.Namespace) -> int:
    extractor = GitExtractor(args.upstream_path, args.downstream_path)
    classifier = DeltaClassifier()
    manager = LedgerManager(args.ledger)

    head_full, head_short = extractor.get_head_sha()
    root_full, root_short = extractor.get_root_commit()
    since_sha = args.since if args.since else root_full

    print(f"Scanning upstream git history ({since_sha[:7]}..{head_short})...")
    raw_commits = extractor.get_commit_log(
        since_sha=None if since_sha == root_full else since_sha, until_sha="HEAD"
    )
    print(f"Found {len(raw_commits)} upstream commits.")

    # Classify commits
    classified_commits: List[CommitEntry] = []
    prs_dict = {}

    for raw in raw_commits:
        entry = classifier.classify_commit(raw)
        classified_commits.append(entry)

        # Track PR if present
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
                )

    pull_requests = sorted(
        list(prs_dict.values()), key=lambda p: p.pr_number, reverse=True
    )

    ledger = manager.initialize_ledger(
        upstream_path=args.upstream_path,
        downstream_path=args.downstream_path,
        baseline_sha=root_full,
        baseline_short_sha=root_short,
        target_sha=head_full,
        target_short_sha=head_short,
        commits=classified_commits,
        prs=pull_requests,
    )

    manager.save(ledger)
    print(
        f"Successfully generated sync ledger at {args.ledger} with {len(classified_commits)} commits and {len(pull_requests)} PRs."
    )
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    manager = LedgerManager(args.ledger)
    if not manager.exists():
        print(f"Error: Sync ledger not found at {args.ledger}.", file=sys.stderr)
        return 1

    try:
        ledger = manager.load()
        ledger.validate_unique_commits(ledger.commits)
        for c in ledger.commits:
            c.validate_invariants()
        print(
            f"Validation successful: {len(ledger.commits)} commits, {len(ledger.pull_requests)} PRs conform to schema invariants."
        )
        return 0
    except Exception as e:
        print(f"Ledger validation failed: {e}", file=sys.stderr)
        return 1


def cmd_report(args: argparse.Namespace) -> int:
    manager = LedgerManager(args.ledger)
    if not manager.exists():
        print(f"Error: Sync ledger not found at {args.ledger}.", file=sys.stderr)
        return 1

    ledger = manager.load()
    generator = ReportGenerator(ledger)
    report_content = generator.generate_parity_report()

    if args.output:
        out_path = Path(args.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"Parity report successfully written to {args.output}")
    else:
        print(report_content)

    if args.generate_issues:
        issue_dir = Path(args.issue_dir).resolve()
        issue_dir.mkdir(parents=True, exist_ok=True)
        specs = generator.generate_all_issue_specs()
        for spec in specs:
            safe_name = "".join(
                ch if ch.isalnum() or ch in "-_" else "_" for ch in spec["short_sha"]
            )
            spec_path = issue_dir / f"port-{safe_name}.md"
            with open(spec_path, "w", encoding="utf-8") as f:
                f.write(f"# {spec['title']}\n\n{spec['body']}")
        print(f"Wrote {len(specs)} GitHub issue specifications to {issue_dir}")

    return 0


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="upstream-sync.py",
        description="TokenTelemetry Upstream Delta Tracking and Sync Ledger Tool",
    )
    parser.add_argument(
        "--ledger",
        default="docs/sync/upstream-ledger.yaml",
        help="Path to the sync ledger YAML file (default: docs/sync/upstream-ledger.yaml)",
    )
    parser.add_argument(
        "--upstream-path",
        default="repositories/tokentelemetry",
        help="Path to upstream submodule repository (default: repositories/tokentelemetry)",
    )
    parser.add_argument(
        "--downstream-path",
        default="repositories/tokentelemetry-go",
        help="Path to downstream Go submodule repository (default: repositories/tokentelemetry-go)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # status subcommand
    p_status = subparsers.add_parser(
        "status", help="Display delta summary and parity metrics"
    )
    p_status.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )

    # list subcommand
    p_list = subparsers.add_parser(
        "list", help="List upstream commits filtered by status or subsystem"
    )
    p_list.add_argument(
        "--status", choices=[s.value for s in StatusEnum], help="Filter by port status"
    )
    p_list.add_argument("--subsystem", help="Filter by subsystem name substring")
    p_list.add_argument("--limit", type=int, default=0, help="Limit number of results")
    p_list.add_argument(
        "--format",
        choices=["table", "json", "markdown"],
        default="table",
        help="Output format",
    )

    # diff subcommand
    p_diff = subparsers.add_parser(
        "diff", help="View patch diff and target Go file mappings"
    )
    p_diff.add_argument("target", help="Commit SHA or PR number to view diff for")

    # triage subcommand
    p_triage = subparsers.add_parser(
        "triage", help="Update porting status of a commit in the ledger"
    )
    p_triage.add_argument("target", help="Commit SHA prefix to triage")
    p_triage.add_argument(
        "--status",
        required=True,
        choices=[s.value for s in StatusEnum],
        help="New port status",
    )
    p_triage.add_argument("--notes", help="Resolution rationale or explanation")
    p_triage.add_argument("--go-commit", help="Go commit SHA where change was ported")
    p_triage.add_argument(
        "--go-pr", type=int, help="Go PR number where change was ported"
    )
    p_triage.add_argument(
        "--issue", type=int, help="Related GitHub issue ID in meta-repo"
    )

    # scan subcommand
    p_scan = subparsers.add_parser(
        "scan", help="Scan local git history and initialize/update sync ledger"
    )
    p_scan.add_argument(
        "--since", help="Earliest commit SHA to scan from (default: root commit)"
    )

    # validate subcommand
    p_validate = subparsers.add_parser(
        "validate", help="Validate ledger schema invariants and uniqueness"
    )

    # report subcommand
    p_report = subparsers.add_parser(
        "report", help="Generate Markdown parity audit report and GitHub issue specs"
    )
    p_report.add_argument(
        "--output",
        help="Output file path for Markdown report (e.g., docs/sync/parity-report.md)",
    )
    p_report.add_argument(
        "--generate-issues",
        action="store_true",
        help="Draft GitHub issue specifications for actionable deltas",
    )
    p_report.add_argument(
        "--issue-dir",
        default="docs/sync/issue-specs",
        help="Output directory for drafted GitHub issue specs (default: docs/sync/issue-specs)",
    )

    return parser


def main() -> int:
    parser = build_cli_parser()
    args = parser.parse_args()

    dispatch = {
        "status": cmd_status,
        "list": cmd_list,
        "diff": cmd_diff,
        "triage": cmd_triage,
        "scan": cmd_scan,
        "validate": cmd_validate,
        "report": cmd_report,
    }

    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
