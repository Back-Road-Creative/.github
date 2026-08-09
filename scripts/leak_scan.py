#!/usr/bin/env python3
"""Check that a public repository publishes its own work and nothing else.

Not a sibling project's name, not a client's name, not the layout of the private
monorepo these repos were extracted from, not a path only real on one laptop.
Three decisions, long form in the repo README:

- The repo's own name is DERIVED from `--self-name`, never configured, so no repo
  is left holding a stale "this is me" setting the scan then stops enforcing.
- A public sibling is not a finding; the public set is read from the API at scan
  time, and if that lookup fails the scan stops rather than guess.
- The gate covers the worktree. `--history` finds published blobs too, but only a
  force-push removes them, so a history gate is permanently red on what no pull
  request can fix — and a red gate gets switched off.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ORG_DEFAULT = "Back-Road-Creative"
MIN_REASON = 20


@dataclass(frozen=True)
class Finding:
    rule: str
    where: str
    path: str
    line: int
    text: str


def build_rules(org: str, self_name: str, public_repos: list[str]) -> list[tuple[str, re.Pattern, str]]:
    """Every rule below fired only on real findings across all thirteen public repos
    when it was written. Candidates that fired on legitimate content — `GMS`,
    `gomoveshift`, `workspaces`, `openclaw`, a bare `/home/<user>/` — were dropped."""
    self_name = self_name.split("/")[-1]  # ${{ github.repository }} is owner/name
    alt = "|".join(re.escape(n) for n in sorted({self_name, *public_repos}, key=len, reverse=True))

    # A repo in this org that is neither this one nor already public. The lookahead
    # has to END the name: `\b` closed it in an earlier version of this rule, and a
    # word boundary sits between `driftless` and the `-` of `driftless-archive`, so
    # the private sibling — the one name the guard existed to keep out of a public
    # snapshot — was the one name it could not see. `.git` passes because a clone
    # URL carries it and still names the repo itself.
    foreign = rf"{re.escape(org)}/(?!(?:{alt})(?:\.git)?(?![\w.-]))[\w.-]+"

    return [
        ("foreign-repo", re.compile(foreign),
         "names a repository in this org that is neither this one nor public"),
        ("client-name", re.compile(r"quasar", re.I),
         "names a third-party client engagement"),
        # Not the general /home/<user>/ shape: these repos document themselves with
        # illustrative paths like /home/user/project, which are examples, not leaks.
        ("machine-path", re.compile(r"/home/(?:joe|dev)(?![\w.-])"),
         "absolute path from an authoring machine"),
        # `pulsar` is unbounded on purpose: it must also catch infrastructure names
        # built from it, such as a storage-account name.
        ("private-project",
         re.compile(r"pulsar|fabric-dev(?![\w.-])|driftless-archive(?![\w.-])", re.I),
         "names a project that exists only in private repositories"),
        # Layout conventions private to the monorepo. `.data/` needs a following path
        # segment (a bare `.gitignore` line names no file); `baton` stays
        # case-sensitive so that a place called Baton Rouge is not a finding.
        ("workspace-convention", re.compile(r"_active/|\.data/[\w.-]+|\bbaton\b"),
         "uses a layout convention private to the monorepo these repos came from"),
    ]


def git(repo: Path, args: list[str]) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          check=True, text=True, errors="replace").stdout


def load_allowlist(path: Path) -> list[dict]:
    """An unexplained exemption is how a guard quietly stops guarding, so a missing
    reason is a hard error and the moment it is added is the only time to demand it."""
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"leak-scan: {path} is not valid JSON: {exc}")
    if not isinstance(entries := data.get("allow", []), list):
        sys.exit(f"leak-scan: {path}: 'allow' must be a list")

    problems = []
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            problems.append(f"entry {i} is not an object")
            continue
        problems += [f"entry {i} has no non-empty '{k}'"
                     for k in ("rule", "path", "match", "reason") if not str(e.get(k, "")).strip()]
        if 0 < len(str(e.get("reason", "")).strip()) < MIN_REASON:
            problems.append(f"entry {i} needs at least {MIN_REASON} characters of reason "
                            "saying why this is safe")
    if problems:
        sys.exit("leak-scan: allowlist is invalid:\n  - " + "\n  - ".join(problems))
    return entries


def is_allowed(f: Finding, entries: list[dict]) -> bool:
    return any(str(e.get("scope", "both")) in ("both", f.where) and e["rule"] == f.rule
               and fnmatch.fnmatch(f.path, e["path"]) and e["match"] in f.text
               for e in entries)


def excerpt(line: str, start: int, end: int, width: int = 90) -> str:
    """Centre the snippet: a line truncated from its left edge hides what is reported."""
    lo, hi = max(0, start - width // 2), min(len(line), end + width // 2)
    return ("…" if lo else "") + line[lo:hi].strip() + ("…" if hi < len(line) else "")


def scan_blob(rules, where: str, path: str, blob: str) -> list[Finding]:
    out = [Finding(rid, where, path, 0, f"<path> {path}")
           for rid, rx, _ in rules if rx.search(path)]
    for n, line in enumerate(blob.splitlines(), start=1):
        line = line[:4000]
        for rid, rx, _ in rules:
            if m := rx.search(line):
                out.append(Finding(rid, where, path, n, excerpt(line, m.start(), m.end())))
    return out


def worktree_blobs(repo: Path, skip: set[str]):
    for rel in git(repo, ["ls-files", "-z"]).split("\0"):
        if not rel or rel in skip:
            continue
        try:
            raw = (repo / rel).read_bytes()
        except OSError:
            continue
        if b"\0" not in raw[:8000]:
            yield rel, raw.decode("utf-8", "replace")


def history_blobs(repo: Path, skip: set[str]):
    """Every blob reachable from every ref, with the path it was stored at."""
    seen: dict[str, str] = {}
    for line in git(repo, ["rev-list", "--all", "--objects"]).splitlines():
        sha, _, rel = line.partition(" ")
        if rel and rel not in skip and sha not in seen:
            seen[sha] = rel
    if not seen:
        return
    buf = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch"],
                         input="\n".join(seen).encode(), capture_output=True,
                         check=True).stdout
    pos = 0
    while (nl := buf.find(b"\n", pos)) != -1:
        header = buf[pos:nl].decode("utf-8", "replace").split()
        pos = nl + 1
        if len(header) < 3:  # "<sha> missing" carries no body
            continue
        sha, kind, size = header[0], header[1], int(header[2])
        body, pos = buf[pos:pos + size], pos + size + 1
        if kind == "blob" and b"\0" not in body[:8000]:
            yield seen.get(sha, sha), body.decode("utf-8", "replace")


def public_repo_names(org: str, given: str | None) -> list[str]:
    if given is not None:
        return [n.strip() for n in given.split(",") if n.strip()]
    try:
        raw = subprocess.run(
            ["gh", "api", f"/orgs/{org}/repos", "--paginate", "--jq",
             '.[]|select(.visibility=="public")|.name'],
            capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        sys.exit(f"leak-scan: could not list this org's public repos ({exc}). Refusing "
                 "to scan: without it a private repo named here would pass as public.")
    if not (names := [n.strip() for n in raw.splitlines() if n.strip()]):
        sys.exit("leak-scan: the org public-repo list came back empty; refusing to scan.")
    return names


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan a repo for another project's content.")
    ap.add_argument("--repo-root", default=".", type=Path)
    ap.add_argument("--self-name", required=True, help="owner/name or name of the repo scanned")
    ap.add_argument("--org", default=ORG_DEFAULT)
    ap.add_argument("--public-repos", help="comma list; omit to query the API")
    ap.add_argument("--allowlist", default=".github/leak-scan-allowlist.json")
    ap.add_argument("--history", action="store_true", help="also scan every blob in history")
    args = ap.parse_args()

    repo, self_name = args.repo_root.resolve(), args.self_name.split("/")[-1]
    rules = build_rules(args.org, self_name, public_repo_names(args.org, args.public_repos))
    entries = load_allowlist(repo / args.allowlist)

    # The allowlist quotes the text it exempts and the scanner spells out every
    # pattern it hunts; scanning either would make both self-incriminating.
    skip = {args.allowlist, "scripts/leak_scan.py", "scripts/test_leak_scan.py",
            ".github/workflows/leak-scan.yml"}

    findings = [f for rel, blob in worktree_blobs(repo, skip)
                for f in scan_blob(rules, "worktree", rel, blob)]
    if args.history:
        findings += [f for rel, blob in history_blobs(repo, skip)
                     for f in scan_blob(rules, "history", rel, blob)]
    kept = sorted({f for f in findings if not is_allowed(f, entries)},
                  key=lambda f: (f.where, f.rule, f.path, f.line))

    if not kept:
        print(f"leak-scan: {self_name}: clean.")
        return 0

    why, current = {rid: text for rid, _, text in rules}, None
    for f in kept:
        if f.rule != current:
            current = f.rule
            print(f"\n{f.rule} — {why[f.rule]}")
        loc = f.path if f.line == 0 else f"{f.path}:{f.line}"
        print(f"  {'' if f.where == 'worktree' else '[history] '}{loc}: {f.text}")
    print(f"\nleak-scan: {self_name}: {len(kept)} finding(s); fix or allowlist in {args.allowlist}.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
