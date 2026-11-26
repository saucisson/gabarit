"""Shared plumbing for every driver command (ADR-0001).

Each module of this package is one driver domain; the plumbing every
driver repeats - the ``.env`` loader, the repository slug, the git
and GitHub runners and the protocol exit codes - lives here once,
so a driver module carries only its own protocol.

Stdlib only, on purpose: every driver imports this module and must
run without any third-party package anywhere (ADR-0001). The GitHub
transport is the ``gh`` CLI called over subprocess: the drivers
inherit its authentication instead of carrying tokens and HTTP
clients of their own.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

ENVIRONMENT_FILE_NAME = ".env"
CLAIM_LABEL_NAME = "night-claimed"

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent

EXIT_CODE_SUCCESS = 0
EXIT_CODE_CRITERIA_UNMET = 1
EXIT_CODE_PROTOCOL_FAILURE = 2


def load_environment_file() -> None:
    """Read KEY=VALUE pairs from .env into the environment if unset.

    The notify tool already loads .env through its settings; these
    commands read it for the same settings. Existing environment
    variables always win.
    """
    environment_path = REPOSITORY_ROOT / ENVIRONMENT_FILE_NAME
    if not environment_path.is_file():
        return
    for raw_line in environment_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def resolve_repository_slug() -> str:
    """Return "owner/repository" from the origin remote, or fail closed."""
    remote_url = try_git(arguments=["remote", "get-url", "origin"]).stdout.strip()
    marker = "github.com"
    separator_index = remote_url.find(marker)
    if separator_index == -1:
        print(
            f"Error: the origin remote is not on GitHub: {remote_url}",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_CODE_PROTOCOL_FAILURE)
    slug = remote_url[separator_index + len(marker) :]
    slug = slug.removeprefix(":").removeprefix("/").removesuffix(".git").strip("/")
    owner, separator, repository = slug.partition("/")
    if not owner or not separator or not repository.strip("/"):
        print(
            f"Error: cannot parse owner/repository from remote: {remote_url}",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_CODE_PROTOCOL_FAILURE)
    return f"{owner}/{repository.strip('/')}"


def try_git(*, arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Run one git command in the repository; the caller checks the exit."""
    return subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def run_git(*, arguments: Sequence[str]) -> str:
    """Run git in the repository, capturing stdout; fail closed."""
    completed_process = try_git(arguments=arguments)
    if completed_process.returncode != EXIT_CODE_SUCCESS:
        print(
            f"Error: git {' '.join(arguments)} failed: {completed_process.stderr.strip()}",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_CODE_PROTOCOL_FAILURE)
    return completed_process.stdout


def try_gh(*, arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Run one gh command in the repository; the caller checks the exit.

    The caller owns the failure policy: a refuse-to-work driver fails
    closed (see ``run_gh_json``), while a warn-and-continue path (the
    night worklist) warns and proceeds.
    """
    return subprocess.run(
        ["gh", *arguments],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def run_gh_json(*, arguments: Sequence[str]) -> object:
    """Run one gh api query and parse its JSON; fail closed."""
    completed_process = try_gh(arguments=arguments)
    if completed_process.returncode != EXIT_CODE_SUCCESS:
        print(
            f"Error: gh {' '.join(arguments)} failed: {completed_process.stderr.strip()}",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_CODE_PROTOCOL_FAILURE)
    try:
        return json.loads(completed_process.stdout)
    except json.JSONDecodeError as error:
        print(
            f"Error: gh {' '.join(arguments)} did not answer JSON: {error}",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_CODE_PROTOCOL_FAILURE) from error


def fetch_pull_request(
    *,
    repository_slug: str,
    pull_request_number: int,
) -> dict[str, object]:
    """Fetch the pull request through gh, or fail closed."""
    pull_request = run_gh_json(
        arguments=["api", f"repos/{repository_slug}/pulls/{pull_request_number}"]
    )
    if not isinstance(pull_request, dict):
        raise SystemExit(EXIT_CODE_PROTOCOL_FAILURE)
    return pull_request


def fetch_check_runs(
    *,
    repository_slug: str,
    head_sha: str,
) -> list[dict[str, object]]:
    """List the CI check runs of the pull request head, or fail closed."""
    payload = run_gh_json(
        arguments=["api", f"repos/{repository_slug}/commits/{head_sha}/check-runs"]
    )
    check_runs = payload.get("check_runs", []) if isinstance(payload, dict) else []
    if not isinstance(check_runs, list):
        return []
    return [entry for entry in check_runs if isinstance(entry, dict)]


def extract_head_sha(*, pull_request: dict[str, object]) -> str:
    """Return the pull request head SHA, or fail closed."""
    head_container = pull_request.get("head")
    head_sha = head_container.get("sha", "") if isinstance(head_container, dict) else ""
    if not head_sha:
        print("Error: the pull request has no head SHA.", file=sys.stderr)
        raise SystemExit(EXIT_CODE_PROTOCOL_FAILURE)
    return head_sha


def extract_head_ref(*, pull_request: dict[str, object]) -> str:
    """Return the pull request head branch name, empty when unknown."""
    head_container = pull_request.get("head")
    return head_container.get("ref", "") if isinstance(head_container, dict) else ""
