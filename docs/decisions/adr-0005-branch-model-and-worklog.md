# ADR-0005: Branch model, merge driver and worklog

- Status: accepted
- Date: 2026-11-06

## Context

Agents must process and merge issues without human intervention during
a working day, while the human keeps meaningful control. Pure
trunk-based removes the control point; per-PR human approval stalls
the day; platform auto-merge gated only on CI enforces nothing. The
human boundary of the protocol is the day (`daily` into `main`), not
the pull request. And `main` moves ONLY through `daily`: every
change - template sync and hotfix included - lands as a pull request
into `daily`, the human merges `daily` into `main` by rebase pull
request, and the branches never diverge. The protocol also
needs a sanctioned write path for pull request bodies (split
proposals) and an audit trail that does not tax every session.

## Decision

- `main` (human merges only, after human tests) / `daily` (the day's
  container, tagged each morning as a restore point) / `feat|fix/<issue>`
  (one issue per branch). After a clean review and green CI, the
  developer agent merges each pull request into `daily` through the
  merge driver (`make merge-pr`): the scripted, criteria-gated action;
  there is no other agent path and no platform auto-merge. Incident
  protocol: revert first, debug second; 3 attempts per issue.
- The merge driver refuses unless ALL hold: the review report exists
  with zero BLOCKING findings, written for THIS pull request and its
  CURRENT head (PR number and head SHA both match, so a stale report
  is never a merge ticket); the pull request is open and mergeable;
  every CI check on its head concluded "success". It then merges
  through the `gh` CLI, `sha` pinned to the reviewed head, with the linear
  method allowed (rebase preferred so nothing is squashed at merge
  time; a squash merge only where rebase is forbidden), and deletes
  the branch.
- `gh pr edit N --body-file ...` is the only body-update path,
  attended or unattended; it REPLACES the whole body (never appends).
- `daily` is never rewritten: with nothing writing `main` outside
  `daily`, it never diverges and only ever moves forward - no
  reconciliation, no sync driver, no force-push in any session.
- **Worklog**: one file per record in `docs/worklog/` - `YYYY-MM-DD-pr-<N>.md`
  per pull request (written from `_template.md` when the pull request
  opens, committed on the branch as
  `worklog: PR #N`), `YYYY-MM-DD-direct-<slug>.md` per direct commit on
  `daily` (from `_template.md`, same commit). No agent reads
  `docs/worklog/`; the evening audit reads the cards and their
  pull requests.

## Consequences

- Agents work autonomously with a blast radius of exactly one day; the
  merge decision is a machine-checkable expression, not agent
  judgement; the day loop integrates each pull request minutes after
  its review.
- Over-budget pull requests have an end-to-end unattended resolution
  (split proposal via `gh pr edit`); with `daily` never rewritten and
  only the merge driver writing it, no concurrent merge can race and
  nothing is left to reconcile.
- The worklog monolith, its unbounded growth, its rebase conflicts and
  its agent-side token drain are gone.
- Negative: a push bypassing the driver is possible in principle - it
  would be a constitutional violation, visible in the history, with
  the end-of-day human review as backstop; the "not on the escalation
  list" criterion stays with the agent's honesty; one merge
  boundary per day means a red morning can cost a day - the
  revert-first protocol and the daily tag make recovery mechanical.
