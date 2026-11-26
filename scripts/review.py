"""Local review orchestrator: one reviewer session per commit (ADR-0006).

``review`` runs on the developer machine, on the pull request branch
checkout: it fetches the pull request through ``gh``, checks the
preconditions (local HEAD pushed, clean tree, CI green on the head),
then reviews the pull request COMMIT BY COMMIT. The developer agent
is expected to have reworked the branch first so each commit explains
itself (one idea, a Conventional Commit message), and
``make probe-merge`` attests every commit green. For each commit the
driver builds one deterministic bundle - the rules corpus, the pull
request goal, that commit's own message, and that commit's diff - and
runs one isolated reviewer session over it (the session machinery
lives in ``scripts/session.py``): the commit message states what the
commit does, and the reviewer judges the diff against that stated
intent. Nothing else enters the prompt: context isolation is
enforced by construction, not by prompt discipline.

Every count is recomputed locally (never trusted from a session);
the aggregated report (one section per commit, plus totals) is what
the merge driver gates on, bound to this pull request and this head
by ``.review/review-context.json`` (ADR-0005). A comment with one
block per commit is posted on the pull request - a posting failure
warns and never masks the verdict. Exit codes: 0 zero BLOCKING, 1
at least one BLOCKING, 2 protocol failure, 3 preconditions unmet
(the head was not pushed or CI had not concluded on it - not a
verdict, not an attempt).

Stdlib only, even for the GitHub transport: ``gh`` is called over
subprocess, never an HTTP client (ADR-0001).
"""

import json
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from scripts import session
from scripts._shared import (
    EXIT_CODE_CRITERIA_UNMET,
    EXIT_CODE_PROTOCOL_FAILURE,
    EXIT_CODE_SUCCESS,
    REPOSITORY_ROOT,
    extract_head_sha,
    fetch_check_runs,
    fetch_pull_request,
    resolve_repository_slug,
    run_git,
    try_gh,
)

if TYPE_CHECKING:
    import argparse
    from collections.abc import Sequence
    from pathlib import Path

REVIEW_DIRECTORY = REPOSITORY_ROOT / ".review"
RULES_DOCUMENT_PATH = REPOSITORY_ROOT / "docs/rules.md"
ENGINEERING_RULES_DOCUMENT_PATH = REPOSITORY_ROOT / "docs/engineering-rules.md"
DECISIONS_DIRECTORY_PATH = REPOSITORY_ROOT / "docs/decisions"
SECTION_SEPARATOR = "\n\n---\n\n"
NO_DESCRIPTION_TEXT = "No pull request description was provided."
SHORT_SHA_LENGTH = 12
EXIT_CODE_FAILURE = EXIT_CODE_CRITERIA_UNMET  # local alias: a bundle component is missing
EXIT_CODE_PRECONDITIONS_UNMET = 3  # the review never started: not a verdict, not an attempt


@dataclass(frozen=True)
class CommitReview:
    """One commit's verified review result."""

    sha: str
    subject: str
    findings: list[session.ReviewFinding]
    counts: dict[session.FindingSeverity, int]


def read_text_file(*, path: Path) -> str:
    """Read one text file, failing loudly on a missing bundle component."""
    if not path.is_file():
        print(f"Error: bundle component missing: {path}", file=sys.stderr)
        raise SystemExit(EXIT_CODE_FAILURE)
    return path.read_text(encoding="utf-8")


def collect_decisions() -> list[tuple[str, str]]:
    """Return every ADR as (title, content), in numeric order."""
    decision_paths = sorted(DECISIONS_DIRECTORY_PATH.glob("adr-*.md"))
    decisions: list[tuple[str, str]] = []
    for decision_path in decision_paths:
        decision_title = decision_path.stem.replace("-", " ").capitalize()
        decisions.append((decision_title, decision_path.read_text(encoding="utf-8")))
    return decisions


def render_bundle(
    *,
    diff_text: str,
    description_text: str,
    decisions: Sequence[tuple[str, str]],
    commit_section: str | None = None,
) -> str:
    """Assemble the bundle sections in a fixed, deterministic order."""
    sections: list[str] = []
    sections.append("## RULES AND CHECKLIST\n\n" + read_text_file(path=RULES_DOCUMENT_PATH))
    sections.append(
        "## ENGINEERING RULES AND CHECKLIST\n\n"
        + read_text_file(path=ENGINEERING_RULES_DOCUMENT_PATH)
    )
    for decision_title, decision_content in decisions:
        sections.append(f"## DECISION - {decision_title}\n\n{decision_content}")
    sections.append(f"## PULL REQUEST GOAL\n\n{description_text}")
    if commit_section is not None:
        sections.append(f"## COMMIT UNDER REVIEW\n\n{commit_section}")
    sections.append(f"## DIFF UNDER REVIEW\n\n{diff_text}")
    return SECTION_SEPARATOR.join(sections)


def review_preconditions_refusal(
    *,
    head_sha: str,
    local_head: str,
    pending_changes: str,
    check_runs: Sequence[dict[str, object]],
) -> str | None:
    """Return the reason the review cannot start; None means: proceed.

    The review is the last gate: it never substitutes for a failing or
    unfinished local gate (ADR-0006). Every refusal exits with code 3
    (preconditions unmet): not a review verdict, not an attempt - the
    developer agent waits (or pushes), then re-runs ``make review``.
    """
    if head_sha != local_head:
        return (
            f"the pull request head {head_sha} is not the local HEAD"
            f" {local_head} - push, wait for CI, then re-run `make review`"
        )
    if pending_changes:
        return (
            "uncommitted changes are present - commit, push, wait for CI, then re-run `make review`"
        )
    if not check_runs:
        return "no CI check runs on the head yet - wait for CI, then re-run `make review`"
    for check_run in check_runs:
        name = str(check_run.get("name", "unnamed check"))
        if check_run.get("status") != "completed":
            return f"CI check {name} is still running - wait for CI, then re-run `make review`"
        if check_run.get("conclusion") != "success":
            return f"CI check {name} did not succeed - fix CI first, then re-run `make review`"
    return None


def load_pr_goal(*, pull_request: dict[str, object]) -> str:
    """Return the pull request goal (title and description)."""
    title = pull_request.get("title")
    title_text = title.strip() if isinstance(title, str) else ""
    description = pull_request.get("body")
    description_text = description.strip() if isinstance(description, str) else ""
    if not description_text:
        description_text = NO_DESCRIPTION_TEXT
    if title_text:
        return f"# {title_text}\n\n{description_text}"
    return description_text


def write_pr_goal(*, goal_text: str, review_directory: Path) -> None:
    """Keep the pull request goal beside the bundles, for the audit."""
    review_directory.mkdir(parents=True, exist_ok=True)
    (review_directory / "pull-request-goal.md").write_text(goal_text, encoding="utf-8")


def list_commit_shas(*, base_ref: str) -> list[str]:
    """List the branch's own commits over the base, oldest first.

    Rebase-only integration means no merge commits ever reach a pull
    request; ``--no-merges`` makes that an invariant instead of a hope.
    """
    run_git(arguments=["fetch", "origin", base_ref])
    raw_output = run_git(
        arguments=["rev-list", "--reverse", "--no-merges", f"origin/{base_ref}..HEAD"]
    )
    return [line.strip() for line in raw_output.splitlines() if line.strip()]


def commit_subject(*, commit_sha: str) -> str:
    """Return the commit's subject line."""
    return run_git(arguments=["show", "-s", "--format=%s", commit_sha]).strip()


def commit_message(*, commit_sha: str) -> str:
    """Return the commit's full message: the claim the reviewer judges."""
    return run_git(arguments=["show", "-s", "--format=%B", commit_sha]).strip()


def commit_diff(*, commit_sha: str) -> str:
    """Return the commit's own diff against its parent."""
    return run_git(arguments=["show", "--no-color", "--format=", commit_sha])


def build_commit_bundle(
    *,
    goal_text: str,
    commit_sha: str,
    commit_message_text: str,
    commit_diff_text: str,
    decisions: Sequence[tuple[str, str]],
) -> str:
    """Build one commit's bundle: the PR goal, the commit's message, its diff."""
    commit_section = f"Commit {commit_sha}\n\n{commit_message_text}"
    return render_bundle(
        diff_text=commit_diff_text,
        description_text=goal_text,
        decisions=decisions,
        commit_section=commit_section,
    )


def finding_payload(*, finding: session.ReviewFinding) -> dict[str, object]:
    """Render one finding as plain JSON data."""
    return {
        "severity": finding.severity.value,
        "file": finding.file,
        "line": finding.line,
        "rule": finding.rule,
        "evidence": finding.evidence,
    }


def render_report_payload(*, commit_reviews: Sequence[CommitReview]) -> dict[str, object]:
    """Aggregate the per-commit reports; the merge driver gates on the totals."""
    all_findings = [
        finding for commit_review in commit_reviews for finding in commit_review.findings
    ]
    total_counts = session.count_by_severity(findings=all_findings)
    return {
        "commits": [
            {
                "sha": commit_review.sha,
                "subject": commit_review.subject,
                "findings": [
                    finding_payload(finding=finding) for finding in commit_review.findings
                ],
                "blocking_count": commit_review.counts[session.FindingSeverity.BLOCKING],
                "to_fix_count": commit_review.counts[session.FindingSeverity.TO_FIX],
                "suggestion_count": commit_review.counts[session.FindingSeverity.SUGGESTION],
            }
            for commit_review in commit_reviews
        ],
        "blocking_count": total_counts[session.FindingSeverity.BLOCKING],
        "to_fix_count": total_counts[session.FindingSeverity.TO_FIX],
        "suggestion_count": total_counts[session.FindingSeverity.SUGGESTION],
    }


def render_review_comment(*, commit_reviews: Sequence[CommitReview]) -> str:
    """Render the aggregated comment: one block per reviewed commit."""
    all_findings = [
        finding for commit_review in commit_reviews for finding in commit_review.findings
    ]
    total_counts = session.count_by_severity(findings=all_findings)
    comment_parts: list[str] = []
    comment_parts.append("## Reviewer agent report")
    comment_parts.append("")
    comment_parts.append(
        f"{len(commit_reviews)} commit(s) reviewed, each by one isolated"
        f" reviewer session: **BLOCKING** {total_counts[session.FindingSeverity.BLOCKING]},"
        f" **TO-FIX** {total_counts[session.FindingSeverity.TO_FIX]},"
        f" **SUGGESTION** {total_counts[session.FindingSeverity.SUGGESTION]}."
    )
    for commit_review in commit_reviews:
        comment_parts.append("")
        comment_parts.append(
            session.render_commit_section(
                commit_label=(
                    f"Commit {commit_review.sha[:SHORT_SHA_LENGTH]}: {commit_review.subject}"
                ),
                findings=commit_review.findings,
                counts=commit_review.counts,
            )
        )
    comment_parts.append("")
    comment_parts.append(
        "The reviewer never merges and never modifies code (ADR-0006)."
        " The merge driver (`make merge-pr`) refuses to merge while any"
        " BLOCKING finding stands (ADR-0005)."
    )
    return "\n".join(comment_parts)


def write_review_context(
    *,
    pull_request_number: int,
    head_sha: str,
    review_directory: Path,
) -> None:
    """Write the review context the merge driver will verify (ADR-0005).

    The report alone cannot prove which pull request it reviewed; this
    context binds it to the pull request number and the exact head SHA
    at review time. The merge driver refuses to merge unless both
    still match - a report for another pull request, or for an older
    head, is stale and the merge is refused.
    """
    review_directory.mkdir(parents=True, exist_ok=True)
    (review_directory / "review-context.json").write_text(
        json.dumps({"pr_number": pull_request_number, "head_sha": head_sha}),
        encoding="utf-8",
    )


def post_review_comment(
    *,
    pull_request_number: int,
    review_directory: Path,
) -> None:
    """Post the review comment through gh; warn, never mask the verdict."""
    comment_path = review_directory / "review-comment.md"
    if not comment_path.is_file():
        print("Warning: no review comment was produced (protocol failure?).")
        return
    completed_process = try_gh(
        arguments=[
            "pr",
            "comment",
            str(pull_request_number),
            "--body-file",
            str(comment_path),
        ]
    )
    if completed_process.returncode != EXIT_CODE_SUCCESS:
        print(
            f"Warning: could not post the review comment"
            f" ({completed_process.stderr.strip()}); the verdict is unchanged,"
            " but the audit trail is incomplete.",
            file=sys.stderr,
        )


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the review subcommand."""
    subparser = subparsers.add_parser(
        "review",
        help="Run the per-commit local review of one pull request (ADR-0006).",
        description="Run the per-commit local review of one pull request (ADR-0006).",
    )
    subparser.add_argument(
        "--pr-number",
        type=int,
        required=True,
        help="Number of the pull request to review.",
    )
    subparser.set_defaults(runner=run_review)


def run_review(*, arguments: argparse.Namespace) -> int:
    """Entry point: pull request number in, aggregated verdict out."""
    repository_slug = resolve_repository_slug()
    pull_request = fetch_pull_request(
        repository_slug=repository_slug,
        pull_request_number=arguments.pr_number,
    )
    head_sha = extract_head_sha(pull_request=pull_request)
    local_head = run_git(arguments=["rev-parse", "HEAD"]).strip()
    pending_changes = run_git(arguments=["status", "--porcelain"]).strip()
    check_runs = fetch_check_runs(
        repository_slug=repository_slug,
        head_sha=head_sha,
    )
    refusal_reason = review_preconditions_refusal(
        head_sha=head_sha,
        local_head=local_head,
        pending_changes=pending_changes,
        check_runs=check_runs,
    )
    if refusal_reason is not None:
        print(f"Review refused: {refusal_reason}.", file=sys.stderr)
        return EXIT_CODE_PRECONDITIONS_UNMET
    base_ref_container = pull_request.get("base")
    base_ref = (
        base_ref_container.get("ref", "daily") if isinstance(base_ref_container, dict) else "daily"
    )
    commit_shas = list_commit_shas(base_ref=base_ref)
    if not commit_shas:
        print(
            "Review refused: the branch has no commits over its base - the"
            " pull request is empty (rebase it, or close it).",
            file=sys.stderr,
        )
        return EXIT_CODE_CRITERIA_UNMET
    goal_text = load_pr_goal(pull_request=pull_request)
    write_pr_goal(goal_text=goal_text, review_directory=REVIEW_DIRECTORY)
    write_review_context(
        pull_request_number=arguments.pr_number,
        head_sha=head_sha,
        review_directory=REVIEW_DIRECTORY,
    )
    decisions = collect_decisions()
    print(
        f"Reviewing PR #{arguments.pr_number} against {base_ref}:"
        f" {len(commit_shas)} commit(s), one reviewer session each."
    )
    commit_reviews: list[CommitReview] = []
    for commit_index, commit_sha in enumerate(commit_shas, start=1):
        bundle_text = build_commit_bundle(
            goal_text=goal_text,
            commit_sha=commit_sha,
            commit_message_text=commit_message(commit_sha=commit_sha),
            commit_diff_text=commit_diff(commit_sha=commit_sha),
            decisions=decisions,
        )
        bundle_path = REVIEW_DIRECTORY / f"commit-{commit_index:02d}.md"
        REVIEW_DIRECTORY.mkdir(parents=True, exist_ok=True)
        bundle_path.write_text(bundle_text, encoding="utf-8")
        answer_text = session.run_reviewer_session(
            model_name=session.load_model_name(),
            bundle_path=bundle_path,
        )
        try:
            findings, counts = session.evaluate_answer(answer_text=answer_text)
        except session.ReviewProtocolError as protocol_error:
            print(
                f"Error: the reviewer answer for commit {commit_sha}"
                f" violated the contract: {protocol_error}",
                file=sys.stderr,
            )
            return EXIT_CODE_PROTOCOL_FAILURE
        commit_reviews.append(
            CommitReview(
                sha=commit_sha,
                subject=commit_subject(commit_sha=commit_sha),
                findings=findings,
                counts=counts,
            )
        )
        print(
            f"Commit {commit_sha[:SHORT_SHA_LENGTH]}:"
            f" {counts[session.FindingSeverity.BLOCKING]} BLOCKING,"
            f" {counts[session.FindingSeverity.TO_FIX]} TO-FIX,"
            f" {counts[session.FindingSeverity.SUGGESTION]} SUGGESTION."
        )
    (REVIEW_DIRECTORY / "review-report.json").write_text(
        json.dumps(render_report_payload(commit_reviews=commit_reviews), indent=2),
        encoding="utf-8",
    )
    (REVIEW_DIRECTORY / "review-comment.md").write_text(
        render_review_comment(commit_reviews=commit_reviews),
        encoding="utf-8",
    )
    post_review_comment(
        pull_request_number=arguments.pr_number,
        review_directory=REVIEW_DIRECTORY,
    )
    all_findings = [
        finding for commit_review in commit_reviews for finding in commit_review.findings
    ]
    if session.count_by_severity(findings=all_findings)[session.FindingSeverity.BLOCKING] > 0:
        return EXIT_CODE_CRITERIA_UNMET
    return EXIT_CODE_SUCCESS
