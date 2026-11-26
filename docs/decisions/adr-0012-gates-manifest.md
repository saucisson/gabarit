# ADR-0012: Gate activation manifest, catalog and shared formats

- Status: accepted
- Date: 2026-11-25

## Context

The template implements its quality gates directly in CI steps and
Python code, with activation implied by the workflow file's
content. Two problems followed. Readability: an agent cannot
answer which gates run on this repository without parsing a
workflow. Duplication: every gate the template does not happen to
implement (a react or rust flavor) exists nowhere, so instances
reimplement or skip. And root sprawl: instance audits
found unexplained top-level entries and files riding along from
Windows checkouts (`Zone.Identifier` alternates), which CI never
saw because nothing checks the root inventory.

The template's target set is three environments, rust, react,
python, and an instance may legitimately run more than one (a rust
domain behind a react front).

## Options considered

1. Keep gates implicit in CI, flavors added per instance ad hoc.
   Rejected: activation stays unreadable, duplication stays.
2. One monolithic gate runner for all environments. Rejected:
   a polyglot runtime to run gates that check other runtimes;
   heavy and brittle.
3. A gate catalog and per-environment flavors specified once, an
   activation manifest per repository, shared data formats, and a
   mechanical root-inventory check. Chosen.

## Decision

- `gates.yaml` at the repository root is the activation manifest:
   the instance's environments (any subset of, or several of,
   python, react, rust) and, per gate, its enable state, flavor,
   and parameters. Disabling a gate requires an ADR reference and
   stays visible with its reason - `gates.yaml` carries it
   verbatim, and the catalog in `docs/gates.md` keeps the list
   honest.
- The gate catalog (gate ids, per-environment flavors) and the
   shared data formats are specified once in `docs/gates.md`:
  - `license-allowlist.txt` - bare SPDX identifiers, one per line,
    comments with `#`; consumed by every license-gate flavor;
  - `platform-lock.txt` - the `pin: <sha>` line and per-domain
    globs; consumed by every pin-verification flavor (ADR-0010).
- Flavors are per environment, in `tools/gates/<env>/`. The
   template ships the react flavor of the N2 license gate
   (`tools/gates/react/n2_license.mjs`, reads `package-lock.json`,
   zero dependency); the python flavors keep running through the
   existing `scripts/` drivers; a rust flavor lands with the first
   rust instance.
- CI checks the tracked top-level entries against
  `allowed-root.txt` (bare names, one per line, comments with `#`)
  and fails on anything unknown.

## Consequences

- Every repository question of the form "which gate runs here"
   has a one-file answer, readable by humans and agents before any
   tool runs; and the reasons carried in `gates.yaml` keep the
   disabled ones visible instead of silently absent.
- The template grows a flavor directory it does not itself
   exercise; that is the point, but each flavor must keep its own
   honest CI story (the react flavor runs `node --check` here, it
   exercises on the first react instance).
- Bootstrap honesty: accepted out-of-band with ADR-0009 to
  ADR-0011 (see ADR-0009). Unifying the existing python
  license-gate driver onto `license-allowlist.txt` is a work
  item on the fresh repository, not a property of this seed.
