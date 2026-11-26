# Gate catalog, flavors and shared data formats

This document specifies the gates an agent-led repository of this
family can run, their per-environment flavors, and the data
formats every flavor shares. Gate activation per repository lives
in `gates.yaml` at the root (ADR-0012): environments, enable
state, flavor, parameters. A disabled gate in `gates.yaml` must
carry its reason (and, outside the template's own bootstrap, an
ADR reference); this catalog lists disabled gates with their
reasons so silence never masquerades as green.

The environments are python, react and rust. An instance declares
any subset, and may declare several (a rust domain behind a react
front, for example). Flavors live under `tools/gates/<env>/`;
python gates run through the existing `scripts/` drivers unless a
reason exists to split them.

## Catalog

| Gate id | Flavor(s) | What it enforces |
| ------- | --------- | ---------------- |
| english-only | agnostic | G4: repository artifacts are English |
| ruff-lint | agnostic | Lint (python ecosystem, CI step) |
| ruff-format | agnostic | Format check (python ecosystem) |
| mypy-strict | python | Strict static typing of the package and tools |
| import-linter-onion | python | The onion import contract |
| pytest-coverage-floor | python | Tests pass, coverage floor met |
| gitleaks | agnostic | No secrets in history |
| pip-audit | python | Lockfile dependency audit (OSV) |
| n2-license | python | N2: dependency licenses are all allowed |
| n2-license-node | react | Same, from `package-lock.json` |
| platform-pin-verify | python | ADR-0010: blobs byte-match the registry pin |
| root-inventory | agnostic | ADR-0012: root equals `allowed-root.txt` |

`n2-license-node` is the reference implementation of a non-python
flavor: zero dependency (`node tools/gates/react/n2_license.mjs`),
reads `package-lock.json` (lockfileVersion 2 or 3), normalizes
license expressions the way the registry does, compares against
`license-allowlist.txt`, and exits 1 naming the offenders.
`rust` flavors (cargo-audit, cargo-deny style) land with the first
rust instance, which owns their ADR (>= 0100).

## Shared data formats

### license-allowlist.txt

Bare SPDX identifiers, one per line, sorted. Comment lines start
with `#`; blank lines are ignored. Every license-gate flavor
(python, node, later rust) consumes this same file, so the
admission judgment lives in one place per repository. When the
platform registry hosts a shared allowlist, the file becomes the
pin-synced copy (ADR-0010).

### platform-lock.txt

The instance's contract with the platform registry (ADR-0010).
Format:

    pin: <registry commit sha>
    <domain>: <space-separated globs the instance consumes>

One `pin` line, then one line per consumed domain. The verify gate
fetches the registry at `pin`, resolves the globs, and checks that
every blob the instance carries is byte-identical to the registry's
at that commit. A pin-sync pull request touches only this file,
`gates.yaml` and the blob manifest; it is the single auto-merge
class (ADR-0010).

### allowed-root.txt

Bare top-level names, one per line. Comment lines start with `#`.
The root-inventory gate compares the tracked top-level entries
against this list and fails on anything unknown (ADR-0012, with
the `*Zone.Identifier` gitignore rule keeping Windows
alternate-data-stream artifacts out entirely).

## Catalog duty

This catalog lists, verbatim from `gates.yaml`: every disabled gate
with its reason, and every enabled gate that did not run (with
why). This is a documentation obligation on the catalog, not a new
gate and not a report driver.
