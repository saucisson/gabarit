# ADR-0011: ADR admission and the draft week

- Status: accepted
- Date: 2026-11-25

## Context

ADRs in the template were flipped to `accepted` at creation time.
The instance audits found decisions recorded as accepted
that the code never followed, and decisions accepted without any
mechanical consequence at all: an ADR as literature. Acceptance had
no cost, therefore no meaning. The fix must keep the human
arbitration cheap (minutes, not a review session) while making
acceptance verifiable.

## Options considered

1. Human reads each ADR and accepts on judgment. Rejected alone:
   judgment without a test drifts back to rubber-stamping.
2. Formal acceptance board, quorum, votes. Rejected: a solo owner;
   theater over substance.
3. An admission test at write time, a seven-day draft window, and a
   reviewer verdict of respected-in-code before acceptance. Chosen.

## Decision

- An ADR is admitted only if reversing the decision next week
   would cost more than writing the ADR today; choices reversible
   by construction go to a worklog card with an Alternative line
   (the template in `docs/worklog/_template.md` carries the field).
- A new ADR opens as `draft` with its date-opened in the header.
   The flip to `accepted` is a driver step requiring all of:
  1. seven days elapsed since opening;
  2. no material change merged on the ADR's domain in the window
     (a merged change to the domain resets the clock);
  3. no open objection;
  4. a green implementation on the domain;
  5. a reviewer verdict of `respected-in-code` on the ADR's code
     anchors: the reviewer cites where the code applies the
     decision. For a negative ADR (a decided abstention), the
     enforcing gate must exist and be named; without one the
     verdict is `not-verifiable`, which is not an acceptance state.
- Rule G2 in `docs/engineering-rules.md` carries this text as the
   single authoritative copy; N1 keeps the human validation of a
   flag separate from ADR acceptance: enabling a flag validates
   behavior, it does not accept an ADR.

## Consequences

- Acceptance becomes rare enough to mean something, and cheap
   enough to happen: the human arbitrates objections and the domain,
   the reviewer and the driver do the checklist work.
- Seven days is deliberately boring; urgency is served by the
   morning directive and the flag mechanism, never by shortening
   the window.
- Bootstrap honesty: accepted out-of-band with ADR-0009,
   ADR-0010 and ADR-0012 (see ADR-0009); it governs every ADR
   opened after instantiation, starting at 0100 in instances.
