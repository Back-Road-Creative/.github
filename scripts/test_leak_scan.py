"""What the scanner must, and must not, call a leak. The negative cases are the
load-bearing ones: an over-eager scanner gets switched off, and a switched-off
scanner protects nothing, so every rejected candidate is pinned below."""

from __future__ import annotations

import pytest
from leak_scan import build_rules

ORG = "Back-Road-Creative"


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
