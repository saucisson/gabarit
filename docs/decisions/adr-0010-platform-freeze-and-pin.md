# ADR-0010: Platform registry, shared-domain freeze and pin sync

- Status: accepted
- Date: 2026-11-25

## Context

Several instances share platform-level domains: the common
authentication architecture (Zitadel), deployment patterns for
linard.fr, and soon others. Today every instance carries its own
copy, and the copies drift.
The instance audits showed two failure modes:
agents patching a shared domain locally instead of fixing it
upstream, and humans losing track of which copy is authoritative.
Pending decisions on the platform repository make any propagated
change premature: work done on shared domains while the registry
decision is open is work thrown away or worse, work that blocks
the decision.

## Options considered

1. Keep per-instance copies, sync by discipline. Rejected: nothing
   mechanical holds the copies together; discipline is the first
   casualty of a busy session.
2. A platform repository consulted by agents of every instance,
   with automated propagation of every change. Rejected as stated:
   automated propagation of non-mechanical change is an agent
   merging `main` by proxy.
3. A platform registry plus a frozen-shared-domain rule, with
   exactly one mechanical auto-merge class: the pin sync. Chosen.

## Decision

- `saucisson/platform` exists to hold the shared platform
   documents and their build/deploy scripts. It is the single
   authoritative copy of every domain it lists as shared.
- Every instance pins the platform in `platform-lock.txt` (format
   in `docs/gates.md`): the registry commit and, per domain, the
   globs the instance consumes. Nothing from the platform reaches
   an instance except through its lock.
- While the registry decision on a domain is pending, the domain
   is frozen in every instance: only edits at the adaptation
   boundary are permitted. Two scheduled morning sessions without
   a production path to a frozen domain is the urgent-escalation
   signal the human sets in the morning directive.
- The single auto-merge exception to ADR-0005 (and to A2 in
   `docs/engineering-rules.md`): a pull request touching only the
   platform pin, the lock globs and the blob manifest, in which
   every changed blob verifies byte-identical against the platform
   registry at the pin, merges without review once CI is green and
   flags are off. The human arbitrated upstream; propagation is
   mechanical. Any divergence from that shape (local drift, an
   instance exception, unverifiable bytes) is `needs-human`.

## Consequences

- Agent sessions in instances get a single consultation point for
   platform questions, and an unambiguous answer to who owns a
   shared fix: the registry.
- The registry dependency makes instance CI honest only if pin
   verification runs there; `gates.yaml` carries that gate.
- Bootstrap honesty: accepted out-of-band with ADR-0009,
   ADR-0011 and ADR-0012 (see ADR-0009).
