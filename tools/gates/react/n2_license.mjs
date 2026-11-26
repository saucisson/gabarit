#!/usr/bin/env node
// N2 license gate, react flavor (ADR-0012).
//
// Reads a package-lock.json (lockfileVersion 2 or 3), collects the
// license of every entry in `packages`, normalizes the expression,
// and compares it against an allowlist of bare SPDX identifiers.
//
// Usage:
//   node tools/gates/react/n2_license.mjs [package-lock.json] \
//        [license-allowlist.txt]
//
// Defaults: ./package-lock.json and ./license-allowlist.txt.
// Exit 0: every license allowed. Exit 1: offenders listed. The
// allowlist format is the shared one (docs/gates.md): bare SPDX
// identifiers, one per line, comments with #, blank lines ignored.
//
// Zero dependency by design: the gate must run in the barest image.

import { readFileSync } from "node:fs";
import process from "node:process";

const LOCK = process.argv[2] || "./package-lock.json";
const ALLOW = process.argv[3] || "./license-allowlist.txt";

function die(message) {
  console.error(`n2-license: ${message}`);
  process.exit(1);
}

function readJson(path) {
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    return die(`cannot read ${path}: ${error.message}`);
  }
}

// Normalize a license expression to a bare SPDX identifier set.
// package-lock entries store a SPDX expression (often with
// parentheses, e.g. "(MIT OR Apache-2.0)"), sometimes an SPDX-ID
// string, sometimes a legacy `licenses` array of {type} objects.
function normLicense(entry) {
  const raw = entry.license
    ?? (Array.isArray(entry.licenses)
      ? entry.licenses.map((item) => item.type).sort().join(" OR ")
      : undefined);
  if (raw === undefined) return "UNLICENSED";
  const text = String(raw).trim();
  if (text === "" || text === "UNLICENSED") return "UNLICENSED";
  // Split on OR at the top level (AND would mean all must hold; the
  // gate fails it as not-a-single-allowlisted-id, which is honest).
  return text.replace(/[()]/g, " ").split(/\s+OR\s+/i).map((id) => id.trim());
}

try {
  const lock = readJson(LOCK);
  if (!lock || typeof lock !== "object") die(`${LOCK}: not a lockfile`);
  const version = lock.lockfileVersion;
  const packages = lock.packages;
  if (version !== 2 && version !== 3) {
    die(`unsupported lockfileVersion ${version} (need 2 or 3)`);
  }
  if (!packages || typeof packages !== "object") {
    die(`${LOCK}: no "packages" map`);
  }

  const allowed = readFileSync(ALLOW, "utf8")
    .split("\n")
    .map((line) => line.replace(/#.*$/, "").trim())
    .filter((line) => line !== "");
  const allowedSet = new Set(allowed);

  const offenders = [];
  for (const [path, entry] of Object.entries(packages)) {
    if (!entry || typeof entry !== "object") continue;
    if (entry.link === true) continue; // symlink stub, no metadata
    const ids = normLicense(entry);
    const ok = ids !== "UNLICENSED" && ids.every((id) => allowedSet.has(id));
    if (!ok) {
      offenders.push({ path, ids: Array.isArray(ids) ? ids : [ids] });
    }
  }

  if (offenders.length > 0) {
    console.error(
      `n2-license: ${offenders.length} entr` +
        `${offenders.length === 1 ? "y" : "ies"} outside ` +
        `${ALLOW}:`,
    );
    for (const { path, ids } of offenders.sort((a, b) =>
      a.path.localeCompare(b.path))) {
      console.error(`  ${path}: ${ids.join(" OR ")}`);
    }
    process.exit(1);
  }
  console.log(
    `n2-license: all ${Object.keys(packages).length} entries allowed`,
  );
} catch (error) {
  die(error.message);
}
