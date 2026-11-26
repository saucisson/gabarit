# Worklog - repository records (human destination)

This folder holds the audit records of the repository, meant for the
human who reviews the day before merging `daily` into `main`.

## Conventions

- `YYYY-MM-DD-pr-<N>.md`: one index card per pull request, written
  from `_template.md` when the pull request opens. The author commits
  it on the PR branch (`worklog: PR #N`) and pushes it.
- `YYYY-MM-DD-direct-<slug>.md`: one entry per direct commit on `daily`
  (revert, docs-only fix, hotfix), created from `_template.md` in the
  same commit.
- `README.md` and `_template.md`: this documentation and the entry
  template for direct commits.

## Rules

- No agent reads this folder: every entry is written from the
  template (at pull request opening, or in the direct commit).
- Never modify an existing entry, never purge one: the git history is
  the tamper-evident backstop.
- The evening audit reads the cards here and their pull requests;
  the day's commits are the rest of the record.
