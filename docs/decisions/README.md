# Architecture Decision Records

An ADR records **why** a choice was made, so it can be revisited later
with the original reasoning in hand - not to freeze it.

## Process (MADR-lite)

Each ADR is one file, `adr-NNNN-short-name.md`, containing:

- **Status**: `accepted` (or `superseded by adr-NNNN`).
- **Date**: the decision date.
- **Context**: the forces at play.
- **Options considered**: with explicit trade-offs, including the
  rejected ones and why.
- **Decision**: the chosen option.
- **Consequences**: including the negatives - every decision has some.

## Rules

- Accepted ADRs are **never edited**. A reversal is a new ADR that
  references and supersedes the old one. Owner-set exceptions are
  recorded here: stale references follow the code, so projects
  instantiated from the template never inherit dead paths.
- Superseded ADRs are removed from the repository; ADR numbers are
  never reused.
- **Numbering**: ADR numbers `0001`-`0099` are reserved for the
  template's own decisions (currently 0001-0012). A project
  instantiated from this template numbers its own, project-specific
  ADRs from `0100` upward, so a template update can add new template
  ADRs without ever colliding with the project's.
- ADRs are constitutional files: agents may **draft** a new ADR inside
  a pull request, but only the human owner accepts it. Draft status is
  explicit at the top of the file.
- "ADR-worthy" changes are on the strict escalation list
  (`docs/protocol.md`).
- The ADRs are **language- and tool-agnostic**: they record the ideas.
  The concrete tools of an instance (its language, linter, type
  checker, test runner) apply the ideas; the template's own Python
  tools are the worked example.

## Index

| ADR      | Decision                                                      |
| -------- | ------------------------------------------------------------- |
| [0001](adr-0001-toolchain-and-tooling.md) | Toolchain and repository tooling: stable standards, committed lockfile, delegated maintenance, one CLI driver package |
| [0002](adr-0002-architecture-and-style.md) | Onion data-first architecture; data and functions over OOP; readability-first style |
| [0003](adr-0003-typing-logging-and-apis.md) | Precise typing with one reference checker; structured logging as executable comments; REST with best practices |
| [0004](adr-0004-quality-and-security-gates.md) | Quality gates, security gates, anti-complacency tests |
| [0005](adr-0005-branch-model-and-worklog.md) | Branch model main/daily/work; criteria-checked merge and body-update paths, branches never diverge; per-record worklog |
| [0006](adr-0006-agent-protocol.md) | Two-agent protocol with isolated per-commit local review, budgets, contact channel, runtime permissions, active CI wait |
| [0007](adr-0007-unattended-loop.md) | Unattended loop: one fresh headless session per item, claims first, recovery, anti-spin |
| [0008](adr-0008-agent-era-engineering-rules.md) | Agent-era engineering rules: token economics, typing/abstraction and test doctrine, durable-data doctrine, review allocation, night-acceptance loop |
| [0009](adr-0009-no-releases.md) | No release machinery: builds are commit SHAs, external milestones are plain git tags |
| [0010](adr-0010-platform-freeze-and-pin.md) | Platform registry, shared-domain freeze and the pin-sync auto-merge class |
| [0011](adr-0011-adr-admission-and-draft-week.md) | ADR admission test and the seven-day draft window with reviewer usage verdict |
| [0012](adr-0012-gates-manifest.md) | Gate activation manifest (gates.yaml), gate catalog, shared data formats, per-environment flavors |
