# ADR-0009: No release machinery

- Status: accepted
- Date: 2026-11-25

## Context

The template carried release automation: release-please
configuration and manifest, release and deploy workflows, and a
release clause in ADR-0001. Auditing the instances showed what it
costs: generated changelogs nobody reads, version
tags drifting from what actually runs, branch protection rules and
token scopes existing only to serve the automation, and CI surface
agents must reason about on every action. No instance has an
external consumer of versioned artifacts: each deployment is built
from an explicitly pinned commit, and humans identify a running
build by its SHA.

## Options considered

1. Keep release-please as-is. Rejected: pure recurring cost, zero
   consumer.
2. Keep releases but run them manually. Rejected: the same history
   and tag questions, now dependent on remembering to run them.
3. Drop release machinery entirely. Chosen.

## Decision

- No release automation ships in the template or in an instance:
   no release tooling, no release workflow, no generated changelogs,
   no version variables gated on a release event. This supersedes
   the release-please clause of ADR-0001.
- A build is identified by its commit SHA. An external milestone
   (a demo, a deployment pin) is a plain git tag created by the
   human on the commit that matters.
- Conventional Commits stay (ADR-0009 in `docs/rules.md` commits
   history readability), for their I3 role - agent-readable intent
   units - not for release generation.

## Consequences

- `release-please-config.json`,
   `.release-please-manifest.json`, the release and deploy
   workflows and all release-oriented references are removed from
   this seed.
- One less credential, one less branch-mutation class, one shorter
   CI file; agents lose nothing they used.
- If an instance ever ships a versioned artifact to an external
   consumer, that instance writes its own ADR (>= 0100) adding the
   minimum machinery then; the template does not carry it speculatively.
- Bootstrap honesty: this ADR is accepted out-of-band, together
   with ADR-0010 to ADR-0012, because it defines the state the seed
   ships and the draft window of ADR-0011 does not yet exist as a
   process at bootstrap time. The draft window applies to every ADR
   opened after instantiation.
