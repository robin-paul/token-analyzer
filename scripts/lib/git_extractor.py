from __future__ import annotations
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple


class GitExtractor:
    def __init__(
        self,
        upstream_path: str = "repositories/tokentelemetry",
        downstream_path: str = "repositories/tokentelemetry-go",
    ):
        self.upstream_path = Path(upstream_path).resolve()
        self.downstream_path = Path(downstream_path).resolve()

    def _run_git(self, args: List[str], cwd: Optional[Path] = None) -> str:
        cmd = ["git"] + args
        work_dir = cwd or self.upstream_path
        res = subprocess.run(
            cmd,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()

    def get_head_sha(self) -> Tuple[str, str]:
        full = self._run_git(["rev-parse", "HEAD"])
        short = self._run_git(["rev-parse", "--short=7", "HEAD"])
        return full, short

    def get_root_commit(self) -> Tuple[str, str]:
        output = self._run_git(["rev-list", "--max-parents=0", "HEAD"])
        lines = output.splitlines()
        root = lines[-1] if lines else ""
        short = root[:7]
        return root, short

    def get_commit_diff(self, sha: str) -> str:
        return self._run_git(["show", "--stat", "--patch", sha])

    def get_commit_log(self, since_sha: Optional[str] = None, until_sha: str = "HEAD") -> List[dict]:
        rev_range = f"{since_sha}..{until_sha}" if since_sha else until_sha
        log_format = "%H%x1f%h%x1f%an <%ae>%x1f%aI%x1f%s%x1f%b%x1e"
        raw_output = self._run_git(["log", "--topo-order", "--reverse", f"--format={log_format}", rev_range])

        records = []
        if not raw_output:
            return records

        raw_commits = raw_output.split("\x1e")
        for chunk in raw_commits:
            chunk = chunk.strip()
            if not chunk:
                continue
            parts = chunk.split("\x1f")
            if len(parts) < 5:
                continue
            sha = parts[0].strip()
            short_sha = parts[1].strip()
            author = parts[2].strip()
            date = parts[3].strip()
            subject = parts[4].strip()
            body = parts[5].strip() if len(parts) > 5 else ""

            # Extract changed files for this commit
            files_out = self._run_git(["diff-tree", "--no-commit-id", "--name-only", "-r", sha])
            files = [f.strip() for f in files_out.splitlines() if f.strip()]

            records.append({
                "sha": sha,
                "short_sha": short_sha,
                "author": author,
                "date": date,
                "subject": subject,
                "body": body,
                "files": files,
            })
        return records
