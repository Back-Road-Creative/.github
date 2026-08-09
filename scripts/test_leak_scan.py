"""What the scanner must, and must not, call a leak. The negative cases are the
load-bearing ones: an over-eager scanner gets switched off, and a switched-off
scanner protects nothing, so every rejected candidate is pinned below."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest
from leak_scan import Finding, build_rules, is_allowed, load_allowlist

ORG = "Back-Road-Creative"
FULL_ENTRY = {
    "rule": "workspace-convention",
    "path": "CHANGELOG.md",
    "match": ".data/plans",
    "reason": "Records that this plan stayed in the monorepo at extraction; ships no file.",
}


def hits(text: str, self_name: str = "driftless") -> set[str]:
    rules = build_rules(ORG, self_name, ["keycut", "rigscore", "driftless"])
    return {rid for rid, rx, _ in rules if rx.search(text)}


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # A repo may always name itself, including as a clone URL.
        (f"{ORG}/driftless", set()),
        (f"https://github.com/{ORG}/driftless.git", set()),
        # THE REGRESSION: `\b` closed this lookahead once, and a word boundary sits
        # between `driftless` and the `-` of `driftless-archive` — so the private
        # sibling was the one name the guard could not see.
        (f"{ORG}/driftless-archive", {"foreign-repo", "private-project"}),
        # A public sibling discloses nothing. A private one does.
        (f"{ORG}/keycut", set()),
        (f"{ORG}/headlessmode", {"foreign-repo"}),
        # The real authoring accounts, but not illustrative paths in documentation.
        ("/home/joe/.claude/agents", {"machine-path"}),
        ("cwd: '/home/dev/workspaces'", {"machine-path"}),
        ("Scanning /home/user/my-project", set()),
        ("/home/developer/thing", set()),
        # Rejected candidates: a fixture name, a public brand, a product, a place.
        ('project = Project(name="GMS")', set()),
        ("the gomoveshift brand site", set()),
        ("~/.openclaw/openclaw.json", set()),
        ("moved to Baton Rouge", set()),
        # A bare .gitignore line names no internal file; a real path does.
        (".data/", set()),
        (".data/plans/2026-05-27-waves.md", {"workspace-convention"}),
        ("_active/svc-gomoveshift-video", {"workspace-convention"}),
        ("hand off the baton", {"workspace-convention"}),
        ("const forbidden = ['quasar', 'pulsar']", {"client-name", "private-project"}),
        ("stpulsardev.blob.core.windows.net", {"private-project"}),
    ],
)
def test_rule_hits(text: str, expected: set[str]) -> None:
    assert hits(text) == expected


def test_self_name_accepts_the_owner_slash_name_form() -> None:
    """The workflow feeds ${{ github.repository }}. Misread that and every repo
    reports itself."""
    assert not hits(f"{ORG}/headlessmode", self_name=f"{ORG}/headlessmode")


@pytest.mark.parametrize(
    "entry",
    [
        {"rule": "client-name", "path": "a.md", "match": "x"},          # no reason
        {"rule": "client-name", "path": "a.md", "match": "x", "reason": "legacy"},  # too short
        {"rule": "client-name", "path": "a.md", "reason": "a" * 30},    # no match string
        {"path": "a.md", "match": "x", "reason": "a" * 30},             # no rule
    ],
)
def test_allowlist_entry_without_a_real_reason_is_fatal(tmp_path, entry) -> None:
    """An unexplained exemption is how a guard quietly stops guarding, so this is a
    hard error rather than a warning — the entry cannot be merged."""
    f = tmp_path / "allow.json"
    f.write_text(json.dumps({"allow": [entry]}))
    with pytest.raises(SystemExit):
        load_allowlist(f)


def test_allowlist_accepts_a_fully_explained_entry(tmp_path) -> None:
    f = tmp_path / "allow.json"
    f.write_text(json.dumps({"allow": [FULL_ENTRY]}))
    assert load_allowlist(f) == [FULL_ENTRY]


def test_absent_allowlist_is_empty_not_an_error(tmp_path) -> None:
    assert load_allowlist(tmp_path / "nope.json") == []


def test_entry_suppresses_only_its_own_rule_path_and_text() -> None:
    """All three must line up, so an entry cannot silently widen into a blanket."""
    f = Finding("workspace-convention", "worktree", "CHANGELOG.md", 9, "see .data/plans/x.md")
    assert is_allowed(f, [FULL_ENTRY])
    assert not is_allowed(replace(f, rule="client-name"), [FULL_ENTRY])
    assert not is_allowed(replace(f, path="OTHER.md"), [FULL_ENTRY])
    assert not is_allowed(replace(f, text="see _active/x"), [FULL_ENTRY])


def test_scope_limits_an_entry_to_one_side_of_the_scan() -> None:
    entry = {**FULL_ENTRY, "scope": "history"}
    f = Finding("workspace-convention", "worktree", "CHANGELOG.md", 9, "see .data/plans/x.md")
    assert not is_allowed(f, [entry])
    assert is_allowed(replace(f, where="history"), [entry])
