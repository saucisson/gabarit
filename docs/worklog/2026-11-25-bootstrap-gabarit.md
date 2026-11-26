# Bootstrap of the gabarit repository

- Date: 2026-11-25
- Type: hotfix
- Scope: whole repository (seed authored outside git; this card
  covers the seed that the fresh repository will commit as its
  first commit)
- Motive: the owner's arbitration of 2026-11-25 produced five
  doctrine decisions (ADR-0009 to ADR-0012, plus the pin-sync
  exception of ADR-0010 in engineering-rules A2) and the name
  Gabarit. The same arbitration ruled the drivers question: a
  capable agent drives `gh` directly, so the wrappers that
  duplicated what `gh` already does are gone from this seed.
  The owner chose to bake the corrections into the seed
  rather than replaying them as pull requests on the fresh
  repository; the trade-off is that this worklog has no PR of its
  own, hence its hotfix type.

- Evidence:
  - Every seed edit was an anchor replacement asserting exactly-one
    match before writing; no broad rewrites.
  - No line in the seed ends with a space (verified over the whole
    tree).
  - Removed (ADR-0009): release-please-config.json,
    .release-please-manifest.json, .github/workflows/release.yml,
    .github/workflows/deploy.yml.
  - Removed (owner arbitration; hosting is GitHub-only):
    .gitlab-ci.yml, .gitlab/, and the GitLab paragraph of
    docs/protocol.md (branch-protection settings for a hosting the
    drivers never targeted).
  - Removed (owner arbitration): the 15 pre-seed pull-request
    worklog cards (`2026-11-25-pr-16.md` to
    `2026-11-25-pr-30.md`). They recorded pull requests and
    commits that do not exist here; the folder's own contract (one
    card per pull request of this repository, git history as the
    tamper-evident backstop) made their presence incoherent in a
    fresh repository. Nothing durable is lost: the settled
    reasoning lives in the ADRs and the code.
  - Removed at the owner's arbitration (a fresh repository has no
    history to point back at): the "Merges: former ADR-NNNN"
    header lines and the condensation date annotations of ADR-0001
    to ADR-0007, and the condensation paragraph of
    docs/decisions/README.md. Adoption dates stay. The folder's
    rule that accepted ADRs are never edited takes effect on the
    fresh repository's history; the seed-time edits in this card
    are the owner's own, recorded here.
  - Removed at the owner's arbitration (wrapper duplication): the
    drivers a capable agent already replaces with `gh` - the
    pull-request, claim, CI-wait and body-update wrappers
    (`scripts/pulls.py`, `scripts/claims.py`, `scripts/ci.py`),
    their shared HTTP plumbing (`scripts/_github.py`), their tests,
    their five make targets, and the `GITHUB_TOKEN` block of
    `.env`. The merge, review and night drivers remain, and now
    speak to GitHub only through the `gh` CLI over subprocess,
    fail closed; no driver carries a token or an HTTP client
    anymore, and the bash allowlist of the runtime profile covers
    `gh`. Pull requests open through `gh pr create`, bodies
    update through `gh pr edit`, claims and the CI watch are
    `gh` label edits and `gh pr checks` - the corpus (ADR-0001,
    ADR-0005, ADR-0006, ADR-0007, protocol.md, rules.md, the two
    night prompts, AGENTS.md, the worklog conventions) was
    de-staled to say so; engineering-rules N6 now makes the
    pull-request worklog card a handwritten template card.
    Editing the accepted ADR bodies at all is the owner's own
    arbitration, recorded here.
  - The merge verdicts are invariant under the transport change:
    a differential harness ran the verdict functions of both the
    previous (httpx) and this (gh) merge driver over the same
    battery (10 evaluate_merge_criteria cases, 5
    check_review_context cases, 3 load-review cases) - identical
    outputs everywhere. A stubbed-subprocess harness then walked
    the new paths: green merge (rebase method, sha pinned to the
    reviewed head, branch deletion called), red CI (exit 1, zero
    gh mutations), an HTTP 405 merge refusal (exit 1), an
    unrelated gh failure (exit 2), the night fetches' warn
    semantics (refusal -> None / empty worklist), and the review
    comment posting (warn, never masking the verdict).
  - Commands recommissioned at the owner's arbitration
    (third ruling of 2026-11-25): `sync-daily` and `day-report` are
    gone. `main` accepts nothing outside `daily` anymore - template
    sync and hotfix are pull requests into `daily` like any change -
    so the branches never diverge and `daily` is never rewritten;
    the human audit reads the worklog cards, the pull requests and
    the commits (I1, N7 and 8.5 amended accordingly; ADR-0005 and
    ADR-0007 de-staled; protocol.md, AGENTS.md, the worklog
    conventions and the night prompts say so; night-issue and
    night-auto now demand commits one idea each, every commit green
    under `make probe-merge`).
  - The review is now per commit (same ruling): the developer agent
    reworks the branch first so every commit is explicable - one
    idea, a Conventional Commit message stating what the commit
    does - `make probe-merge` attests every commit green, and
    `make review` runs one isolated reviewer session per commit,
    each seeing only the pull request goal, that commit's message
    (the claim the diff is judged against) and that commit's diff.
    `review-bundle` and the `agent-review` subcommand are absorbed
    into `review` (`session.py` is internal machinery, no CLI);
    ADR-0006, ADR-0008, rules.md and protocol.md carry the new
    contract, exit codes now including 3 (preconditions unmet).
  - Stubbed-transport harness of the per-commit review driver, 23
    checks: preconditions refusals (head not pushed, CI
    unconcluded) exit 3 writing nothing; an empty pull request
    exits 1 with no session run; two clean commits exit 0, bundles
    one per commit, oldest first, each isolated (no bundle ever
    contains another commit's diff) and holding the goal, the
    commit message and that commit's diff; a BLOCKING answer exits
    1 with the finding attributed to the right commit; an
    off-contract answer exits 2; a failed comment posting warns
    without masking the verdict; fenced JSON answers parse.
  - Post-publication fix, found while checking the session-launch
    contract against the CLI's documented programmatic mode:
    run_reviewer_session compared the session exit status against
    `EXIT_CODE_REVIEWED_CLEAN`, a constant the per-commit rewrite
    had removed - a NameError on the first real reviewer session,
    invisible to py_compile (the failing line sits in a function
    body) and to the stubbed harness (the runner itself was
    stubbed). Now compared against 0, the CLI's documented exit
    code for "the agent finished". A second harness then exercised
    the real runner with only subprocess stubbed: a finished
    session launches the documented contract (--prompt-file,
    --system-prompt-file, --output json, --max-turns, --time-limit,
    conditional --model and --max-tokens) and parses through
    extract_answer_text; a failed session (documented exit 3)
    raises the protocol failure, exit 2.
  - Post-publication de-stale (found while drafting the real-world
    test scenarios): the branch-protection instructions still allowed
    force pushes on `daily` `--force-with-lease`, for the removed
    sync driver (README, protocol.md, and two Consequences bullets of
    ADR-0005). With branches-never-diverge there is nothing left to
    force-push: protections now forbid it on both branches, and no
    concurrent merge can race.
  - At the owner's arbitration, VALIDATION gains a blocking general
    rehearsal on a throwaway repository, before the definitive
    initial commit: SR-0 environment, SR-1 one real isolated reviewer
    session (contract command, hand-built bundle, time-limit
    variant), SR-2 real precondition refusals, SR-3 one real
    per-commit review (structural invariants only - the literal
    findings of a real model are recorded, never predicted), SR-4 the
    tampered-context merge refusal then the real merge, SR-5
    probe-merge, SR-6 the first night as a non-blocking observation.
    The seed's oracle stays the byte manifest; the rehearsal is where
    the live transports (the `vibe` session, `gh`) run for the first
    time. The card and corpus of the seed are unchanged by it.
  - De-staled docs/protocol.md against the code: both merge-method
    descriptions (the driver, scripts/merge.py
    MERGE_METHOD_PREFERENCE, and I3 are rebase-first, squash only
    where rebase is forbidden) and the branch-protection section.
  - De-staled two clauses of ADR-0005's body at the owner's
    arbitration: the "release" species in the enumeration of what
    moves `main` without `daily` (removed - ADR-0009 ended that
    species), and the merge-method parenthetical (rebase
    preferred, squash only where rebase is forbidden - the ADR now
    matches the driver, I3 and protocol.md instead of
    contradicting all three).
  - Root inventory replayed locally before archiving: 19
    top-level entries, 19 allowed, 0 unknown, 0 stale.
  - tools/gates/react/n2_license.mjs: `node --check` passes;
    smoke-tested on a fabricated lockfileVersion 3 lock: MIT and
    "(MIT)" normalize identically, a legacy `licenses` array
    merges, `link: true` stubs are skipped, UNLICENSED entries are
    flagged, an allowlist violation exits 1 naming the offender,
    lockfileVersion 1 is refused.
  - The seed verifies byte for byte against MANIFEST.sha1
    (88/88, verify.py shipped beside the tree).
- Known limits:
  - The gh transport was never executed against a real repository:
    no `gh` binary exists in the authoring sandbox. Verified
    locally instead: py_compile of every edited module, the
    differential verdict battery, and the stubbed-subprocess
    harness described above. The first CI run and the first live
    night on the fresh repository validate the real transport; a
    red CI there is a deviation to report, not to fix.
  - A `gh` merge refusal is classified by reading the CLI stderr
    (an HTTP 405 refusal is criteria unmet, anything else is
    protocol failure): gh gives no structured status code.
    Documented in the merge_pull_request docstring.
  - The per-commit review flow was exercised only through the
    stubbed harness: no `gh` binary and no `vibe` CLI exist in the
    authoring sandbox, so no real reviewer session ever ran, and
    one reviewer session per commit is the accepted cost. The
    first real pull request on the fresh repository arbitrates.
  - The python gates were not executed locally: the local
    interpreter (3.12) cannot import scripts/ (the unparenthesized
    multi-exception except clauses parse only from Python 3.14,
    documented in the scripts/english.py docstring). CI is the
    arbiter; the validation report must record the version used.
  - The existing python license-gate driver still carries its own
    allowlist instead of reading license-allowlist.txt; unifying it
    is a work item on the fresh repository (ADR-0012 names it).
  - Disabled-gate visibility (ADR-0012) now rests on the record
    itself: the reason sits verbatim in `gates.yaml`, and
    `docs/gates.md` carries the list. No driver enforces the sync;
    the fresh repository's humans do.
  - platform-lock.txt does not exist yet (registry pending,
    ADR-0010); the platform-pin-verify gate is disabled with
    reason in gates.yaml.
  - ADR-0001 still mentions release-please in its historical text;
    ADRs are immutable records, and ADR-0009 supersedes that
    clause explicitly.
  - Provenance was purged at the owner's instruction: this card
    cites neither any pre-seed repository nor the arbitration
    discussion. The trade-off is explicit - a worklog normally
    keeps provenance; here the owner ruled the fresh repository
    starts with no external history, and the ruling itself is
    recorded here as the provenance.
- Alternative: shipping the seed as an unamended base and
  replaying the corrections as reviewed pull requests on the fresh
  repository; rejected by the owner (automation cost of five review
  round-trips on content already arbitrated), knowing the cost:
  this bootstrap trusts the seed verification instead of the review
  pipeline it recommends everywhere else (ADR-0011).
