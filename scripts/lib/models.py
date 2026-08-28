from __future__ import annotations
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class StatusEnum(str, Enum):
    ACTIONABLE_DELTA = "actionable_delta"
    PORTED = "ported"
    IN_PROGRESS = "in-progress"
    DEFERRED = "deferred"
    SKIPPED_NOT_APPLICABLE = "skipped_not_applicable"


class SubsystemType(str, Enum):
    BACKEND_PARSERS = "backend/parsers"
    BACKEND_PRICING = "backend/pricing"
    BACKEND_STORE = "backend/store"
    BACKEND_API = "backend/api"
    BACKEND_MODELS = "backend/models"
    FRONTEND_INSPECTOR = "frontend/inspector"
    FRONTEND_ANALYTICS = "frontend/analytics"
    FRONTEND_DASHBOARD = "frontend/dashboard"
    PACKAGING_PYTHON = "packaging/python"
    PACKAGING_FRONTEND = "packaging/frontend"
    INFRA_TOOLING = "infra/tooling"
    DOCS_DOMAIN = "docs/domain"
    DOCS_MARKETING = "docs/marketing"
    DEPRECATED_HERMES = "deprecated/hermes"
    OTHER = "other"


class CommitCategory(str, Enum):
    FEAT = "feat"
    FIX = "fix"
    CHORE = "chore"
    DOCS = "docs"
    REFACTOR = "refactor"
    TEST = "test"
    BUILD = "build"
    CI = "ci"
    PERF = "perf"
    MERGE = "merge"
    OTHER = "other"


class ResolutionInfo(BaseModel):
    notes: str = ""
    go_commit_sha: Optional[str] = None
    go_pr_number: Optional[int] = None
    github_issue_id: Optional[int] = None


class CommitEntry(BaseModel):
    sha: str
    short_sha: str
    author: str
    date: str
    message: str
    category: str = "other"
    scope: Optional[str] = None
    pr_number: Optional[int] = None
    subsystems: List[str] = Field(default_factory=list)
    status: StatusEnum = StatusEnum.ACTIONABLE_DELTA
    confidence_score: float = 1.0
    target_go_files: List[str] = Field(default_factory=list)
    resolution: ResolutionInfo = Field(default_factory=ResolutionInfo)

    def validate_invariants(self) -> None:
        if self.status in (StatusEnum.SKIPPED_NOT_APPLICABLE, StatusEnum.DEFERRED):
            if not self.resolution or not self.resolution.notes or not self.resolution.notes.strip():
                raise ValueError(
                    f"Commit {self.short_sha} with status '{self.status.value}' must have non-empty resolution notes."
                )
        if self.status == StatusEnum.PORTED:
            if not self.resolution or (
                not self.resolution.go_commit_sha
                and not self.resolution.go_pr_number
                and not self.resolution.notes.strip()
            ):
                raise ValueError(
                    f"Ported commit {self.short_sha} must supply go_commit_sha, go_pr_number, or resolution notes."
                )


class PullRequestEntry(BaseModel):
    pr_number: int
    title: str
    author: str
    branch: Optional[str] = None
    merge_commit_sha: Optional[str] = None
    subsystems: List[str] = Field(default_factory=list)
    status: StatusEnum = StatusEnum.ACTIONABLE_DELTA
    summary: str = ""
    target_go_files: List[str] = Field(default_factory=list)
    resolution: ResolutionInfo = Field(default_factory=ResolutionInfo)


class RepositoryInfo(BaseModel):
    upstream_path: str
    downstream_path: str
    baseline_commit: str
    baseline_short_sha: str
    baseline_tag_or_label: Optional[str] = None
    target_commit: str
    target_short_sha: str


class SummaryInfo(BaseModel):
    total_commits: int = 0
    total_pull_requests: int = 0
    actionable_delta_count: int = 0
    ported_count: int = 0
    in_progress_count: int = 0
    deferred_count: int = 0
    skipped_not_applicable_count: int = 0
    un_triaged_count: int = 0
    parity_percentage: float = 100.0


class UpstreamLedger(BaseModel):
    schema_version: str = "1.0.0"
    generated_at: str = ""
    last_updated_at: str = ""
    repository: RepositoryInfo
    summary: SummaryInfo
    pull_requests: List[PullRequestEntry] = Field(default_factory=list)
    commits: List[CommitEntry] = Field(default_factory=list)

    @staticmethod
    def validate_unique_commits(commits: List[CommitEntry]) -> None:
        seen = set()
        for c in commits:
            if c.sha in seen:
                raise ValueError(f"Duplicate commit SHA in ledger: {c.sha}")
            seen.add(c.sha)
