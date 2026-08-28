from __future__ import annotations
import re
from typing import List, Optional, Tuple
from scripts.lib.models import (
    CommitCategory,
    CommitEntry,
    ResolutionInfo,
    StatusEnum,
    SubsystemType,
)

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s+(?P<subject>.+)$",
    re.IGNORECASE,
)
PR_MERGE_RE = re.compile(
    r"^Merge pull request #(?P<pr>[0-9]+) from (?P<branch>.+)$",
    re.IGNORECASE,
)
PR_SQUASH_RE = re.compile(r"\(#(?P<pr>[0-9]+)\)$")


class DeltaClassifier:
    def parse_conventional_message(self, message: str) -> Tuple[str, Optional[str], Optional[int]]:
        category = "other"
        scope = None
        pr_number = None

        m_merge = PR_MERGE_RE.match(message)
        if m_merge:
            return "merge", None, int(m_merge.group("pr"))

        m_squash = PR_SQUASH_RE.search(message)
        if m_squash:
            pr_number = int(m_squash.group("pr"))

        m_conv = CONVENTIONAL_RE.match(message)
        if m_conv:
            category = m_conv.group("type").lower()
            scope = m_conv.group("scope")
            if scope:
                scope = scope.lower()

        return category, scope, pr_number

    def map_paths_to_subsystems(self, files: List[str]) -> List[str]:
        subsystems = set()
        for f in files:
            f_lower = f.lower()
            if "backend/summarizers/" in f_lower:
                subsystems.add("backend/parsers")
            elif "backend/pricing" in f_lower:
                subsystems.add("backend/pricing")
            elif "backend/history_store" in f_lower or "migrations" in f_lower:
                subsystems.add("backend/store")
            elif "backend/tt_paths" in f_lower:
                subsystems.add("backend/models")
            elif "backend/main.py" in f_lower:
                subsystems.add("backend/api")
            elif "frontend/src/app/sessions" in f_lower or "frontend/src/components/session" in f_lower:
                subsystems.add("frontend/inspector")
            elif "frontend/src/app/analytics" in f_lower or "frontend/src/components/analytics" in f_lower:
                subsystems.add("frontend/analytics")
            elif "frontend/src/app/projects" in f_lower or "frontend/src/components/project" in f_lower:
                subsystems.add("frontend/dashboard")
            elif "requirements" in f_lower or "pyproject.toml" in f_lower:
                subsystems.add("packaging/python")
            elif "package.json" in f_lower or "package-lock.json" in f_lower or "next.config" in f_lower:
                subsystems.add("packaging/frontend")
            elif "hermes" in f_lower:
                subsystems.add("deprecated/hermes")
            elif "website/" in f_lower or "docs/" in f_lower:
                subsystems.add("docs/marketing")
            elif "bin/cli.js" in f_lower or "docker" in f_lower or "makefile" in f_lower:
                subsystems.add("infra/tooling")
            else:
                subsystems.add("other")

        return sorted(list(subsystems))

    def map_target_go_files(self, subsystems: List[str]) -> List[str]:
        targets = set()
        for s in subsystems:
            if s == "backend/parsers":
                targets.add("internal/scanner/parsers/")
            elif s == "backend/pricing":
                targets.add("internal/pricing/engine.go")
            elif s == "backend/store":
                targets.add("internal/store/sessions.go")
            elif s == "backend/models":
                targets.add("internal/models/session.go")
            elif s == "backend/api":
                targets.add("internal/api/routes.go")
            elif s == "frontend/inspector":
                targets.add("frontend/src/components/session/")
            elif s == "frontend/analytics":
                targets.add("frontend/src/components/analytics/")
            elif s == "frontend/dashboard":
                targets.add("frontend/src/components/dashboard/")
        return sorted(list(targets))

    def classify_commit(self, raw: dict) -> CommitEntry:
        message = raw.get("subject", "")
        files = raw.get("files", [])
        category, scope, pr_number = self.parse_conventional_message(message)
        subsystems = self.map_paths_to_subsystems(files)
        target_go_files = self.map_target_go_files(subsystems)

        status = StatusEnum.ACTIONABLE_DELTA
        notes = ""

        # Classification heuristics
        if any(s in ("packaging/python", "packaging/frontend", "deprecated/hermes", "docs/marketing") for s in subsystems) and not any(s in ("backend/parsers", "backend/pricing", "backend/store", "frontend/inspector") for s in subsystems):
            status = StatusEnum.SKIPPED_NOT_APPLICABLE
            notes = "Upstream packaging/tooling/marketing change not applicable to Go architecture."
        elif category in ("chore", "docs") and not any(s in ("backend/parsers", "backend/pricing", "backend/store") for s in subsystems):
            status = StatusEnum.SKIPPED_NOT_APPLICABLE
            notes = "Upstream documentation or routine chore."
        elif category == "merge":
            status = StatusEnum.PORTED
            notes = "Git merge commit."
        else:
            status = StatusEnum.ACTIONABLE_DELTA
            notes = f"Actionable upstream change ({category}) requiring Go porting."

        return CommitEntry(
            sha=raw.get("sha", ""),
            short_sha=raw.get("short_sha", ""),
            author=raw.get("author", ""),
            date=raw.get("date", ""),
            message=message,
            category=category,
            scope=scope,
            pr_number=pr_number,
            subsystems=subsystems,
            status=status,
            confidence_score=0.95,
            target_go_files=target_go_files,
            resolution=ResolutionInfo(notes=notes),
        )
